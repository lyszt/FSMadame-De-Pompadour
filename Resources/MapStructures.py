from typing import List, Callable, Optional

class MapInteraction:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.action: Callable = lambda x: x+1 # placeholder while undefined

class LocationNode:
    def __init__(self, index, interactables, doors, accessible: bool, actors: Optional[List["Humanoid"]] = None):
        # This structure represents the list of possible actions inside a location
        self.interactables: List[MapInteraction] = interactables if interactables is not None else []
        # This structure represents a possible teleport/location you can get to
        # Use empty list if none provided
        self.doors: List[LocationNode] = doors if doors is not None else []
        self.index = index
        self.accessible = accessible
        # actors present in an area in any given point
        self.actors: List["Humanoid"] = actors if actors else []

    def add_interactable(self, interactable: "MapInteraction"):
        self.interactables.append(interactable)

    def add_door(self, node: "LocationNode"):
        self.doors.append(node)

    def add_actor(self, actor: "Humanoid"):
        self.actors.append(actor)

    def get_visible_actors(self, actor_node: "LocationNode") -> List["Humanoid"]:
        visible = actor_node.actors.copy()  # actors in the same room
        for neighbor in actor_node.doors:    # actors in adjacent rooms
            visible.extend(neighbor.actors)
        return visible


    def __repr__(self):
        return f"LocationNode(index={self.index}, doors={[d.index for d in self.doors]})"


class MapStructure:
    def __init__(self, size):
        self.map_matrix: List[List[LocationNode]] = [
            [LocationNode(index=(r * size + c), interactables=[], doors=[], accessible=True, actors=[]) for c in range(size)]
            for r in range(size)
        ]

    def add_interactable_to_area(self, index_x: int, index_y: int, interactable: MapInteraction):
            self.map_matrix[index_x][index_y].add_interactable(interactable)

    def add_door_to_area(self, index_x: int, index_y: int, door: LocationNode):
        self.map_matrix[index_x][index_y].add_door(door)

    def add_door_to_area(self, index_x: int, index_y: int, door: LocationNode):
        self.map_matrix[index_x][index_y].add_door(door)