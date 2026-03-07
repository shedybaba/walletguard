"""
One-time script: Build a risk scoring ONNX model and upload to OpenGradient Model Hub.

The model takes portfolio weights and per-asset volatilities, then outputs:
  - portfolio_volatility: sqrt(sum((w_i * vol_i)^2))
  - hhi: sum(w_i^2)  (Herfindahl-Hirschman Index)
  - max_weight: max(w_i)

Usage:
    export OG_PRIVATE_KEY="0x..."
    python models/build_onnx.py
"""

import os
import onnx
from onnx import helper, TensorProto


def build_onnx_model(output_path="risk_scorer.onnx"):
    """
    Build a minimal ONNX model.

    Inputs:
      - weights: float32[1, N]
      - volatilities: float32[1, N]

    Outputs:
      - risk_scores: float32[1, 3]  -> [portfolio_vol, hhi, max_weight]
    """
    # Inputs
    weights_input = helper.make_tensor_value_info("weights", TensorProto.FLOAT, [1, None])
    vols_input = helper.make_tensor_value_info("volatilities", TensorProto.FLOAT, [1, None])

    # Output
    risk_output = helper.make_tensor_value_info("risk_scores", TensorProto.FLOAT, [1, 3])

    # Axis tensor for reductions along dimension 1
    axes_tensor = helper.make_tensor("axes_1", TensorProto.INT64, [1], [1])

    # 1. weighted_vols = weights * volatilities
    mul_node = helper.make_node("Mul", ["weights", "volatilities"], ["weighted_vols"])

    # 2. wv_squared = weighted_vols^2
    sq_node = helper.make_node("Mul", ["weighted_vols", "weighted_vols"], ["wv_squared"])

    # 3. port_var = sum(wv_squared) along axis 1
    reduce_var = helper.make_node("ReduceSum", ["wv_squared", "axes_1"], ["port_var"], keepdims=1)

    # 4. port_vol = sqrt(port_var)
    sqrt_node = helper.make_node("Sqrt", ["port_var"], ["port_vol"])

    # 5. weights_sq = weights^2
    wsq_node = helper.make_node("Mul", ["weights", "weights"], ["weights_sq"])

    # 6. hhi = sum(weights_sq) along axis 1
    reduce_hhi = helper.make_node("ReduceSum", ["weights_sq", "axes_1"], ["hhi"], keepdims=1)

    # 7. max_weight = max(weights) along axis 1
    reduce_max = helper.make_node("ReduceMax", ["weights", "axes_1"], ["max_weight"], keepdims=1)

    # 8. Concat [port_vol, hhi, max_weight] -> risk_scores [1, 3]
    concat_node = helper.make_node("Concat", ["port_vol", "hhi", "max_weight"], ["risk_scores"], axis=1)

    graph = helper.make_graph(
        [mul_node, sq_node, reduce_var, sqrt_node, wsq_node, reduce_hhi, reduce_max, concat_node],
        "RiskScorer",
        [weights_input, vols_input],
        [risk_output],
        [axes_tensor],
    )

    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)])
    model.ir_version = 8
    onnx.checker.check_model(model)
    onnx.save(model, output_path)
    print(f"[+] ONNX model saved to {output_path}")
    return output_path


def upload_to_opengradient(onnx_path):
    """Upload the ONNX model to OpenGradient Model Hub."""
    import opengradient as og

    private_key = os.environ.get("OG_PRIVATE_KEY")
    if not private_key:
        print("[!] OG_PRIVATE_KEY not set. Skipping upload.")
        print("[!] Set it and re-run to upload, or manually upload via the Model Hub UI.")
        return None

    client = og.Client(private_key=private_key)

    repo = client.model_hub.create_model_repo(
        name="walletguard-risk-scorer",
        description="Portfolio risk scoring model: outputs volatility, HHI, and composite risk",
    )
    print(f"[+] Model repo: {repo}")

    version = client.model_hub.upload_model(
        repo_name="walletguard-risk-scorer",
        model_path=onnx_path,
    )
    print(f"[+] Model uploaded. CID: {version.cid}")
    print(f"    Set this in your environment:")
    print(f"    export RISK_MODEL_CID={version.cid}")
    return version.cid


if __name__ == "__main__":
    path = build_onnx_model()
    upload_to_opengradient(path)
