import pandas as pd
import math
from core.elements import Network, SignalInformation

net = Network("resources/nodes.json")
node_labels = list(net.nodes.keys())

results = []

# --- Iterate over all source–destination pairs ---
for i, src in enumerate(node_labels):
    for dst in node_labels[i+1:]:
        # Find all possible paths between src and dst
        paths = net.find_paths(src, dst)

        for path in paths:
            # Create a new signal (1 mW = 1e-3 W)
            sig = SignalInformation(signal_power=1e-3, path=path.copy())

            # Propagate through the network
            net.propagate(sig)

            # Compute SNR (avoid log of zero)
            if sig.noise_power > 0:
                snr_linear = sig.signal_power / sig.noise_power
                snr_db = 10 * math.log10(snr_linear)
            else:
                snr_db = float("inf")

            # Format path string as "A->B->C"
            path_str = "->".join(path)

            # Store results
            results.append({
                "path": path_str,
                "latency": sig.latency,
                "noise": sig.noise_power,
                "SNR": snr_db
            })

df = pd.DataFrame(results)
df_sorted = df.sort_values(by="SNR", ascending=False)

df_sorted["latency"] = df_sorted["latency"].round(5)
df_sorted["noise"] = df_sorted["noise"].round(5)
df_sorted["SNR"] = df_sorted["SNR"].round(5)

df_sorted.to_csv("results/metrics.csv", index=False)
