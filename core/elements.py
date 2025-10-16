import math
import json
from .math_utils import FIBER_SPEED
import matplotlib.pyplot as plt
from typing import Dict

class SignalInformation:
    def __init__(self, signal_power: float, path: list[str]):
        self.signal_power: float = float(signal_power)
        self.noise_power: float = 0.0
        self.latency: float = 0.0
        self.path: list[str] = list(path)

    def add_signal_power(self, increment: float):
        self.signal_power += increment

    def add_noise_power(self, increment: float):
        self.noise_power += increment

    def add_latency(self, increment: float):
        self.latency += increment

    def drop_node(self):
        if self.path:
            self.path.pop(0)

    def next_node(self):
        if self.path:
            return self.path[0]

class Node:
    def __init__(self, params: dict):
        self.label: str = params["label"]
        self.position: tuple[float, float] = params["position"]
        self.connected_nodes: list[str] = params["connected_nodes"]
        self.successive: dict = {}

    def propagate(self, signal):
        signal.drop_node()
        next_node = signal.next_node()
        if next_node is not None:
            line = self.successive[next_node]
            line.propagate(signal)

class Line:
    def __init__(self, label: str, length: float):
        self.label = label
        self.length = float(length)
        self.successive = {}

    def latency_generation(self):
        return (self.length * 1000) / FIBER_SPEED

    def noise_generation(self, signal_power: float):
        return 1e-9 * signal_power * self.length

    def propagate(self, signal):
        # update signal latency and noise
        signal.add_latency(self.latency_generation())
        signal.add_noise_power(self.noise_generation(signal.signal_power))

        # forward to the next node
        next_node = signal.next_node()
        if next_node is not None:
            self.successive[next_node].propagate(signal)


class Network:
    def __init__(self, nodes_json_path: str = "resources/nodes.json"):
        # load topology
        with open(nodes_json_path, "r") as f:
            data = json.load(f)

        # create Node instances
        self.nodes: Dict[str, Node] = {}
        for label, info in data.items():
            self.nodes[label] = Node({
                "label": label,
                "position": tuple(info["position"]),  # (x, y) in meters
                "connected_nodes": list(info["connected_nodes"])
            })

        # create directed Line instances (UV and VU) with Euclidean distance in km
        self.lines: Dict[str, Line] = {}
        for u, info in data.items():
            x1, y1 = info["position"]
            for v in info["connected_nodes"]:
                x2, y2 = data[v]["position"]
                dist_m = math.hypot(x2 - x1, y2 - y1)
                length_km = dist_m / 1000.0
                label_uv = f"{u}{v}"
                if label_uv not in self.lines:
                    self.lines[label_uv] = Line(label_uv, length_km)

        self.connect()

    def connect(self):
        for n in self.nodes.values():
            n.successive = {}
        for l in self.lines.values():
            l.successive = {}

        for line_label, line in self.lines.items():
            if len(line_label) < 2:
                continue
            u, v = line_label[0], line_label[1]
            if u in self.nodes and v in self.nodes:
                self.nodes[u].successive[v] = line
                line.successive[v] = self.nodes[v]

    def find_paths(self, src: str, dst: str):
        if src not in self.nodes or dst not in self.nodes:
            return []

        paths = [[src]]
        valid_paths = []

        while paths:
            current_path = paths.pop(0)
            last_node = current_path[-1]

            if last_node == dst:
                valid_paths.append(current_path)
                continue

            for nbr in self.nodes[last_node].connected_nodes:
                if nbr not in current_path:  # avoid loops
                    new_path = current_path + [nbr]
                    paths.append(new_path)

        return valid_paths

    def propagate(self, signal: SignalInformation) -> SignalInformation:
        if not signal.path:
            return signal

        start_label = signal.path[0]
        self.nodes[start_label].propagate(signal)
        return signal

    def draw(self):
        for label, node in self.nodes.items():
            x, y = node.position
            plt.scatter([x], [y])
            plt.text(x, y, label, fontsize=10, ha="right", va="bottom")

        drawn = set()
        for line_label in self.lines:
            if len(line_label) < 2:
                continue
            u, v = line_label[0], line_label[1]
            key = tuple(sorted((u, v)))
            if key in drawn:
                continue
            x1, y1 = self.nodes[u].position
            x2, y2 = self.nodes[v].position
            plt.plot([x1, x2], [y1, y2])
            drawn.add(key)

        plt.xlabel("x (m)")
        plt.ylabel("y (m)")
        plt.title("Optical Network")
        plt.axis("equal")
        plt.tight_layout()
        plt.show()






