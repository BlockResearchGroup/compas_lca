"""
Some notes:

There are several classes we need to consider:

1. LcaMaterial (pure)
2. LcaComposite (multiple LcaMaterial mixed)
3. LcaComponent (component as stored in EPD or inventory, e.g., window or door)

Then, an LcaElement can either be made from
1. One LcaMaterial
2. One LcaComposite
3. Multiple LcaLayer

And an LcaLayer can be either made from:
1. One LcaMaterial
2. One LcaComposite

These classes are high-level concepts still
Better to create separate classes instead of trying to address everything in MaterialSpec
"""