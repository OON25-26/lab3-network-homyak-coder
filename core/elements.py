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

    # getters
    def get_signal_power(self) -> float:
        return self.signal_power

    def get_noise_power(self) -> float:
        return self.noise_power

    def get_latency(self) -> float:
        return self.latency

    def get_path(self) -> list[str]:
        return list(self.path)

    # setters
    def set_signal_power(self, value: float) -> None:
        self.signal_power = float(value)

    def set_noise_power(self, value: float) -> None:
        self.noise_power = float(value)

    def set_latency(self, value: float) -> None:
        self.latency = float(value)

    def set_path(self, path: list[str]) -> None:
        self.path = list(path)

    # other logic
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

    # getters
    def get_label(self) -> str:
        return self.label

    def get_position(self) -> tuple[float, float]:
        return self.position

    def get_connected_nodes(self) -> list[str]:
        return list(self.connected_nodes)

    def get_successive(self) -> dict:
        return self.successive

    # setters
    def set_label(self, value: str) -> None:
        self.label = str(value)

    def set_position(self, pos: tuple[float, float]) -> None:
        self.position = (float(pos[0]), float(pos[1]))

    def set_connected_nodes(self, neighbors: list[str]) -> None:
        self.connected_nodes = list(neighbors)

    def set_successive(self, mapping: dict) -> None:
        self.successive = dict(mapping)

    # propagation
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

    # getters
    def get_label(self) -> str:
        return self.label

    def get_length(self) -> float:
        return self.length

    def get_successive(self) -> dict:
        return self.successive

    # setters
    def set_label(self, value: str) -> None:
        self.label = str(value)

    def set_length(self, value: float) -> None:
        self.length = float(value)

    def set_successive(self, mapping: dict) -> None:
        self.successive = dict(mapping)

    # calculations
    def latency_generation(self):
        return (self.length * 1000) / FIBER_SPEED

    def noise_generation(self, signal_power: float):
        return 1e-9 * signal_power * self.length

    # signal propagation
    def propagate(self, signal):
        signal.add_latency(self.latency_generation())
        signal.add_noise_power(self.noise_generation(signal.signal_power))
        next_node = signal.next_node()
        if next_node is not None:
            self.successive[next_node].propagate(signal)



class Network:
    def __init__(self, nodes_json_path: str = "resources/nodes.json"):
        with open(nodes_json_path, "r") as f:
            data = json.load(f)
        self.nodes: Dict[str, Node] = {}
        for label, info in data.items():
            self.nodes[label] = Node({
                "label": label,
                "position": tuple(info["position"]),
                "connected_nodes": list(info["connected_nodes"])
            })
        self.lines: Dict[str, Line] = {}
        for a, info in data.items():
            x1, y1 = info["position"]
            for b in info["connected_nodes"]:
                x2, y2 = data[b]["position"]
                dist_m = math.hypot(x2 - x1, y2 - y1)
                length_km = dist_m / 1000.0
                label = f"{a}{b}"
                if label not in self.lines:
                    self.lines[label] = Line(label, length_km)
        self.connect()

    def connect(self):
        for n in self.nodes.values():
            n.successive = {}
        for l in self.lines.values():
            l.successive = {}
        for line_label, line in self.lines.items():
            if len(line_label) < 2:
                continue
            a, b = line_label[0], line_label[1]
            if a in self.nodes and b in self.nodes:
                self.nodes[a].successive[b] = line
                line.successive[b] = self.nodes[b]

    def find_paths(self, src: str, dst: str):
        if src not in self.nodes or dst not in self.nodes:
            return []
        paths = [[src]]
        final_paths = []
        while paths:
            current_path = paths.pop(0)
            last_node = current_path[-1]
            if last_node == dst:
                final_paths.append(current_path)
                continue
            for nbr in self.nodes[last_node].connected_nodes:
                if nbr not in current_path:
                    new_path = current_path + [nbr]
                    paths.append(new_path)
        return final_paths

    def propagate(self, signal: SignalInformation):
        start_label = signal.path[0]
        self.nodes[start_label].propagate(signal)

    # getters
    def get_nodes(self) -> Dict[str, Node]:
        return self.nodes

    def get_lines(self) -> Dict[str, Line]:
        return self.lines

    # setters
    def set_nodes(self, nodes: Dict[str, Node]) -> None:
        self.nodes = nodes

    def set_lines(self, lines: Dict[str, Line]) -> None:
        self.lines = lines

    def draw(self):
        for label, node in self.nodes.items():
            x, y = node.position
            plt.plot(x, y, "o")
            plt.text(x, y, label)
        for a, node in self.nodes.items():
            for b in node.connected_nodes:
                if a < b:  # not duplicate them
                    x1, y1 = node.position
                    x2, y2 = self.nodes[b].position
                    plt.plot([x1, x2], [y1, y2])
        plt.title("Optical Network from Lab 3")
        plt.savefig("results/topology.png", dpi=300)






