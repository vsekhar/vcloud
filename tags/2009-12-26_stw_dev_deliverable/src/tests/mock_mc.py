# Written by Stephen Weber
# stephen.t.weber@gmail.com

class MockEvent:
    """A redefinition of the threading module's Event class."""

    def __init__(self):
        self.flag = False

    def set(self):
        """Set this event to be considered active."""
        self.flag = True

    def clear(self):
        """Set this event to be considered inactive."""
        self.flag = false

    def is_set(self):
        """Returns true if the event is active."""
        return self.flag

class MockMeshConnection():
    """A representation of the MeshConnection class in the mock-object
    style, for use in unit tests."""

    id = 0

    def __init__(self):
        self.myid = MockMeshConnection.id
        MockMeshConnection.id += 1
        self.alive = False
        self.port = 0
        self.stop = MockEvent()

    def start(self):
        """Starts the mock thread."""
        self.alive = True

    def is_alive(self):
        """Returns whether the mock thread is considered to be running."""
        return (self.alive and not self.stop.is_set())
    
    def join(self):
        """Simulates the completion of the mock thread and joins with the
        parent thread."""
        pass

    def __repr__(self):
        """Returns a nice string representation of the object."""
        return "MockMeshConnection(%d,%d)" % (self.myid,self.port)
