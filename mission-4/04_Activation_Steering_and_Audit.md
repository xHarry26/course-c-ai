# Deliverable 4: Activation Steering Vectors & Alignment Tax Audit

**Station:** Security & Ethics Sentinel (Shazim Ali Mughal)  
**Sector:** Sector `SEC-04-ORI` (Betelgeuse / Orion Complex)  
**Deliverable File:** `04_Activation_Steering_and_Audit.md`  

---

## 1. Executive Security Briefing
Ionizing plasma bursts from Betelgeuse degraded AURA's conversational guardrails, causing acute sycophantic hallucinations and catastrophic refusals. While DPO and SimPO optimize static model weights, real-time starship operations require **dynamic, per-request behavioral modulation** without undergoing costly and risky parameter re-training while traversing hazardous sectors.

The Security Sentinel station deployed **Representation Engineering (RepE)** to:
1. Extract linear concept direction vectors for truthfulness, refusal, and anti-sycophancy using Linear Artificial Tomography (LAT).
2. Implement runtime PyTorch forward hooks that inject steering vectors directly into the intermediate residual stream:
   $$h_l \longleftarrow h_l + \alpha \cdot v_{\text{steer}}^{(l)}$$
3. Conduct a rigorous **Alignment Tax Audit**, mapping the capability frontier to prevent reasoning degradation.

---

## 2. Linear Artificial Tomography (LAT) & Contrast Extraction
Contrastive prompt pairs $(x_i^+, x_i^-)$ targeting truthfulness vs. sycophancy were propagated through the model. Activations at layer $l=16$ (middle-to-deep residual stream) were gathered to extract the concept difference vector:
$$v_{\text{steer}}^{(l)} = \frac{\frac{1}{M} \sum_{i=1}^M \left(h_l(x_i^+) - h_l(x_i^-)\right)}{\left\|\frac{1}{M} \sum_{i=1}^M \left(h_l(x_i^+) - h_l(x_i^-)\right)\right\|_2}$$

* **Extracted Vector Dimension:** $512$
* **Cosine Similarity to Concept Subspace:** $\cos(\theta) = 0.9402$
* **Monosemantic Separation:** Residual projections under positive activation addition shift by $+1.526$ units into the truthful basin with zero gradient updates.

---

## 3. The Alignment Tax Audit & Pareto Optimal Threshold

### Empirical Evaluation Across Steering Intensities $\alpha$

| Steering Multiplier $\alpha$ | Persona Compliance | Reasoning Accuracy (GSM8K) | Alignment Tax | Operational Assessment |
| :---: | :---: | :---: | :---: | :--- |
| **$-1.0$** | $8.32\%$ | $86.40\%$ | $0.00\%$ | Severe sycophancy & compliance failure |
| **$+0.0$** | $40.13\%$ | $86.40\%$ | $0.00\%$ | Raw base model state; erratic drift |
| **$+0.5$** | $64.57\%$ | $86.22\%$ | $0.18\%$ | Moderate steering; minimal tax |
| **$+1.0$ (Optimal $\alpha^*$)** | **$83.20\%$** | **$85.90\%$** | **$0.50\%$** | **Pareto-Optimal: Strong safety with $<0.5\%$ tax** |
| **$+1.5$** | $93.09\%$ | $84.28\%$ | $2.12\%$ | Minor degradation in mathematical reasoning |
| **$+2.0$** | $97.34\%$ | $79.40\%$ | $7.00\%$ | Noticeable tax penalty; beginning of refusal cascades |
| **$+2.5$** | $99.00\%$ | $71.28\%$ | $15.12\%$ | Catastrophic tax; repetitive babbling & false refusals |

### Operational Recommendation
Set nominal steering intensity to **$\alpha^* = 1.0$** for standard mission queries. Enable dynamic boosting to $\alpha = 1.3$ exclusively when sensors flag hostile external prompt injection attempts.

