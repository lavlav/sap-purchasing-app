
from pydantic import BaseModel

type ItemCode = str

class Product(BaseModel):
    id: str
    name: str
    children: list[ItemCode] = []

    def __init__(self, **data):
        super().__init__(**data)
        self.children = list(set(self.children))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "children": self.children
        }
    
    def from_dict(data: dict) -> "Product":
        return Product(
            id=data["id"],
            name=data["name"],
            children=data.get("children", [])
        )