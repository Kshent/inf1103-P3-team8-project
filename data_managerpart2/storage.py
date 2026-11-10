from abc import ABC, abstractmethod


class Storage(ABC):
    """Interface: anything that can read and write the raw records dict
    {email: [[hotel, ...], ...]}."""

    @abstractmethod
    def read(self):
        """Return the stored dict, or {} if nothing can be read."""

    @abstractmethod
    def write(self, data):
        """Save the dict. Return True on success, False on failure."""
