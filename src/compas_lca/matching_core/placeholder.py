# note: just adding some important thoughts here for documentation
# there's three different "types" of matching within LCA workflows
#   1. Either its stored as a "pure" material within the inventory
#   2. Or it is a composite material, where there's 2 or more "pure" materials that need to be matched
#   3. Or it is stored as a component, typically windows or doors.
# it will be important to distinguish these, and the problem is that there should be different "containers" (and perhaps matching cores) for each scenario
# so for instance, LcaMaterial corresponds to "concrete", but will it correspond to "reinforced concrete"?
# and if its a "door" or a "window", LcaMaterial doesnt make much sense (but also storing it as an LcaElement with a "material" is difficult)
# perhaps we should consider introducing an LcaComponent as well, and branch the inference / extraction early (i.e., with a TypeAgent, which figures out if its a pure material, composite, or component)
# if we can allocate the proper "type" of building model data (or EPD data) early, it increases precision, but also creates more branches again...