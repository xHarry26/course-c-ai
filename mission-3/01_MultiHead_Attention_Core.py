#!/usr/bin/env python3
"""
USSE Noosphere - Subsystem 03 Restoration
Deliverable 1: Systems Architect (Lead Engineer)
File: 01_MultiHead_Attention_Core.py

Implements Scaled Dot-Product & Multi-Head Self-Attention from scratch in pure PyTorch:
- Explicit linear projection matrices (W_Q, W_K, W_V, W_O)
- Multi-head partitioning: (batch, num_heads, seq_len, head_dim)
- Causal masking support
- Empirical unit test verifying variance preservation under 1/sqrt(d_k) scaling
"""

import math
from typing import Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class ScaledDotProductAttention(nn.Module):
    """
    Scaled Dot-Product Attention:
    Attention(Q, K, V) = softmax( (Q @ K.T) / sqrt(d_k) + M ) @ V
    """
    def __init__(self, dropout: float = 0.0):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        query: [batch, num_heads, seq_len_q, head_dim]
        key:   [batch, num_heads, seq_len_k, head_dim]
        value: [batch, num_heads, seq_len_v, head_dim]
        mask:  Optional mask broadcastable to [batch, num_heads, seq_len_q, seq_len_k]
        """
        d_k = query.size(-1)
        scale = 1.0 / math.sqrt(d_k)

        # 1. Compute raw affinity logits: [batch, num_heads, seq_len_q, seq_len_k]
        scores = torch.matmul(query, key.transpose(-2, -1)) * scale

        # 2. Apply causal or padding mask
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        # 3. Softmax over key sequence dimension
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # 4. Context aggregation: [batch, num_heads, seq_len_q, head_dim]
        context = torch.matmul(attention_weights, value)
        return context, attention_weights


class MultiHeadSelfAttention(nn.Module):
    """
    Multi-Head Self-Attention constructed from scratch.
    Linearly projects inputs into Q, K, V across h parallel heads.
    """
    def __init__(
        self,
        d_model: int,
        num_heads: int,
        dropout: float = 0.0,
        bias: bool = False,
    ):
        super().__init__()
        assert d_model % num_heads == 0, f"d_model ({d_model}) must be divisible by num_heads ({num_heads})"

        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        # Linear projections
        self.w_q = nn.Linear(d_model, d_model, bias=bias)
        self.w_k = nn.Linear(d_model, d_model, bias=bias)
        self.w_v = nn.Linear(d_model, d_model, bias=bias)
        self.w_o = nn.Linear(d_model, d_model, bias=bias)

        self.attention = ScaledDotProductAttention(dropout=dropout)

        self._reset_parameters()

    def _reset_parameters(self):
        # Xavier uniform initialization for projection weights
        nn.init.xavier_uniform_(self.w_q.weight)
        nn.init.xavier_uniform_(self.w_k.weight)
        nn.init.xavier_uniform_(self.w_v.weight)
        nn.init.xavier_uniform_(self.w_o.weight)

    def forward(
        self,
        x: torch.Tensor,
        is_causal: bool = False,
        custom_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        x: [batch_size, seq_len, d_model]
        Returns:
            output: [batch_size, seq_len, d_model]
            attn_weights: [batch_size, num_heads, seq_len, seq_len]
        """
        batch_size, seq_len, _ = x.shape

        # 1. Project to Q, K, V
        q = self.w_q(x)  # [batch, seq_len, d_model]
        k = self.w_k(x)
        v = self.w_v(x)

        # 2. Reshape into parallel heads: (batch, num_heads, seq_len, head_dim)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        # 3. Construct causal mask if requested
        mask = custom_mask
        if is_causal:
            # Lower-triangular causal mask: 1 where allowed, 0 where masked
            causal_mask = torch.tril(torch.ones((seq_len, seq_len), device=x.device, dtype=torch.bool))
            causal_mask = causal_mask.unsqueeze(0).unsqueeze(0)  # [1, 1, seq_len, seq_len]
            if mask is not None:
                mask = mask & causal_mask
            else:
                mask = causal_mask

        # 4. Scaled Dot-Product Attention across all heads
        context, attn_weights = self.attention(q, k, v, mask=mask)

        # 5. Concatenate heads: [batch, seq_len, num_heads * head_dim = d_model]
        context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)

        # 6. Final linear projection W_O
        output = self.w_o(context)
        return output, attn_weights


# ==============================================================================
# UNIT TESTS & VARIANCE PRESERVATION VERIFICATION
# ==============================================================================

def run_variance_preservation_test():
    """
    Mathematically verifies:
    If elements of q and k are independent ~ N(0, 1),
    Var(q . k) = d_k, and Var((q . k) / sqrt(d_k)) = 1.0.
    """
    print("--------------------------------------------------------------------------------")
    print("TEST 1: Variance Preservation Property of 1/sqrt(d_k)")
    print("--------------------------------------------------------------------------------")
    torch.manual_seed(42)
    sample_sizes = [32, 64, 128, 256, 512]
    num_samples = 100000

    print(f"{'Head Dim (d_k)':<16} | {'Raw Var(q.k)':<18} | {'Theoretical d_k':<18} | {'Scaled Var(q.k / sqrt(d_k))':<28}")
    print("-" * 86)
    for d_k in sample_sizes:
        q = torch.randn(num_samples, d_k)
        k = torch.randn(num_samples, d_k)

        # Raw dot product
        raw_dot = torch.sum(q * k, dim=-1)
        raw_var = torch.var(raw_dot).item()

        # Scaled dot product
        scaled_dot = raw_dot / math.sqrt(d_k)
        scaled_var = torch.var(scaled_dot).item()

        print(f"{d_k:<16} | {raw_var:<18.2f} | {float(d_k):<18.2f} | {scaled_var:<28.4f}")
        assert abs(scaled_var - 1.0) < 0.05, f"Variance scaling failed for d_k={d_k}: {scaled_var}"

    print(">>> SUCCESS: 1/sqrt(d_k) restores unit variance across all test head dimensions! <<<\n")


def run_multihead_attention_shape_and_causal_test():
    """
    Verifies tensor shapes and causal autoregressive masking.
    """
    print("--------------------------------------------------------------------------------")
    print("TEST 2: MultiHeadSelfAttention Forward & Causal Masking")
    print("--------------------------------------------------------------------------------")
    batch_size = 2
    seq_len = 8
    d_model = 64
    num_heads = 4

    mha = MultiHeadSelfAttention(d_model=d_model, num_heads=num_heads)
    mha.eval()

    x = torch.randn(batch_size, seq_len, d_model)

    # 1. Non-causal forward pass
    out, weights = mha(x, is_causal=False)
    assert out.shape == (batch_size, seq_len, d_model), f"Output shape mismatch: {out.shape}"
    assert weights.shape == (batch_size, num_heads, seq_len, seq_len), f"Weights shape mismatch: {weights.shape}"
    print(f"[*] Non-Causal Output Shape: {list(out.shape)} - PASSED")
    print(f"[*] Non-Causal Attention Weights Shape: {list(weights.shape)} - PASSED")

    # 2. Causal forward pass
    out_causal, weights_causal = mha(x, is_causal=True)
    assert out_causal.shape == (batch_size, seq_len, d_model)

    # Verify causal upper-triangle is strictly 0.0
    upper_tri = torch.triu(weights_causal, diagonal=1)
    max_leakage = upper_tri.max().item()
    print(f"[*] Causal Masking Upper Triangle Maximum Weight: {max_leakage:.6f}")
    assert max_leakage == 0.0, f"Causal leakage detected: {max_leakage}"
    print(">>> SUCCESS: Causal mask strictly blocks attention to future positions! <<<\n")


if __name__ == "__main__":
    print("================================================================================")
    print("  USSE NOOSPHERE • SYSTEMS ARCHITECT DELIVERABLE")
    print("  01_MultiHead_Attention_Core.py Verification Battery")
    print("================================================================================")
    run_variance_preservation_test()
    run_multihead_attention_shape_and_causal_test()
    print("================================================================================")
    print("  DELIVERABLE 01 COMPLETE: All unit tests passed without external wrappers.")
    print("================================================================================")
