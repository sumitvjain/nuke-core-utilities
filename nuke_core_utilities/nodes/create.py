import nuke
import os


def create_node(node_class, name=None, xpos=None, ypos=None):
    """
    Create a Nuke node safely with optional name and position.

    Args:
        node_class (str): Nuke node class name (e.g. 'Grade', 'Merge').
        name (str, optional): Name for the node.
        xpos (int, optional): X position in node graph.
        ypos (int, optional): Y position in node graph.

    Returns:
        nuke.Node: Created node, or None if creation fails.
    """
    try:
        node = nuke.createNode(node_class, inpanel=False)

        if name is not None:
            node.setName(name)

        if xpos is not None:
            node.setXpos(int(xpos))

        if ypos is not None:
            node.setYpos(int(ypos))

        return node

    except Exception as e:
        nuke.warning("Failed to create node {}: {}".format(node_class, e))
        return None


def create_read(path, colorspace=None):
    """
    Create a Read node with file path and optional colorspace.

    Args:
        path (str): File path to read (image sequence or single file).
        colorspace (str, optional): Colorspace name (e.g. 'ACES - ACEScg').

    Returns:
        nuke.Node: Created Read node, or None if creation fails.
    """
    if not path:
        nuke.warning("create_read: Empty path provided")
        return None

    if not os.path.exists(path):
        nuke.warning("create_read: Path does not exist: {}".format(path))
        return None

    try:
        read = nuke.createNode("Read", inpanel=False)
        read["file"].fromUserText(path)

        if colorspace:
            try:
                read["colorspace"].setValue(colorspace)
            except Exception:
                nuke.warning(
                    "Colorspace '{}' not available on this Read node".format(colorspace)
                )

        return read

    except Exception as e:
        nuke.warning("Failed to create Read node: {}".format(e))
        return None


def create_write(path, file_type="exr"):
    """
    Create a Write node with defaults. Auto-connect Input if node selected. 

    Args:
        path (str): Output file path (can include frame padding).
        file_type (str): File type (exr, png, jpg, mov, etc).

    Returns:
        nuke.Node: Created Write node, or None if creation fails.
    """
    if not path:
        nuke.warning("create_write: Empty output path")
        return None

    try:
        write = nuke.createNode("Write", inpanel=False)

        # Set file path
        write["file"].fromUserText(path)

        # File type
        if "file_type" in write.knobs():
            write["file_type"].setValue(file_type)

        # ---- Defaults for EXR ----
        if file_type.lower() == "exr":
            if "channels" in write.knobs():
                write["channels"].setValue("rgba")

            if "datatype" in write.knobs():
                write["datatype"].setValue("16 bit half")

            if "compression" in write.knobs():
                write["compression"].setValue("Zip (16 scanlines)")

        sel = nuke.selectedNode()
        if sel:
            write.setInput(0, sel[0])


        return write

    except Exception as e:
        nuke.warning("Failed to create Write node: {}".format(e))
        return None
