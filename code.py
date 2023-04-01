from random import choices, uniform
from math import radians
from mathutils import Euler, Vector
from mathutils.noise import noise_vector, noise
import bpy


class TreeGrammar:
    """docstring for TreeGrammar"""
    def __init__(self, parameters):
        self.start               = parameters["start"]
        self.stop                = parameters["stop"]
        self.initial_width       = parameters["initial_width"]
        self.max_recursion_depth = parameters["max_recursion_depth"]
        self.grammar             = parameters["grammar"]
        self.geometries          = parameters["geometries"]


    def draw(self):
        initial_width = uniform(self.initial_width[0], self.initial_width[1])
        self.turtle(recursion_depth=0, symbol=self.start, width=initial_width, angle=(0,0,0), position=(0,0,0))


    def turtle(self, recursion_depth, symbol, width, angle, position):
        if recursion_depth > self.max_recursion_depth:
            return

        if symbol in self.stop:
            return

        for rule in self.grammar:
            if rule["input"] == symbol:
                outputs = choices(rule["output"], rule["likelihood"])[0]

        for output in outputs:
            for geometry in self.geometries:
                if geometry["input"]==symbol and geometry["output"]==output:
                    new_width, new_angle, new_position = self.drawBranch(geometry, recursion_depth, width, angle, position)
                    self.turtle(recursion_depth + 1, output, new_width, new_angle, new_position)


    def drawBranch(self, geometry, recursion_depth, width, angle, position):
        angle_x   = radians(uniform(geometry["angle"][0][0], geometry["angle"][0][1])) * (geometry["reduce_angle"][0] ** recursion_depth)
        angle_y   = radians(uniform(geometry["angle"][1][0], geometry["angle"][1][1])) * (geometry["reduce_angle"][1] ** recursion_depth)
        angle_z   = radians(uniform(geometry["angle"][2][0], geometry["angle"][2][1])) * (geometry["reduce_angle"][2] ** recursion_depth)
        length    = uniform(geometry["length"][0], geometry["length"][1]) * (geometry["reduce_length"] ** recursion_depth)

        branch_vector = Vector((0, 0, length))
        branch_euler_new  = Euler((angle_x , angle_y , angle_z ), "XYZ")
        branch_euler_old  = Euler((angle[0], angle[1], angle[2]), "XYZ")
        branch_vector.rotate(branch_euler_new)
        branch_vector.rotate(branch_euler_old)
        
        reference_vector = Vector((0, 0, length))
        new_angle = reference_vector.rotation_difference(branch_vector).to_euler('XYZ')[:]
        new_position  = (position[0]+branch_vector[0], position[1]+branch_vector[1], position[2]+branch_vector[2])

        bpy.ops.curve.primitive_nurbs_path_add(enter_editmode=True) 
        curve = bpy.context.active_object
        points = curve.data.splines[0].points

        noise_constant = uniform(geometry["curve"][0], geometry["curve"][1]) * length / 7
        points[0].co = Vector((    position[0],     position[1],     position[2], 1))
        points[4].co = Vector((new_position[0], new_position[1], new_position[2], 1))
        points[1].co = points[0].co.lerp(points[4].co, 0.25) + noise_constant * noise_vector(points[0].co.lerp(points[4].co, 0.25).xyz).to_4d()
        points[2].co = points[0].co.lerp(points[4].co, 0.50) + noise_constant * noise_vector(points[0].co.lerp(points[4].co, 0.50).xyz).to_4d()
        points[3].co = points[0].co.lerp(points[4].co, 0.75) + noise_constant * noise_vector(points[0].co.lerp(points[4].co, 0.75).xyz).to_4d()

        curve.data.bevel_depth = width * geometry["reduce_width_begin"]
        points[0].radius = 1.00 + 0.00 * geometry["reduce_width_end"]
        points[1].radius = 0.75 + 0.25 * geometry["reduce_width_end"]
        points[2].radius = 0.50 + 0.50 * geometry["reduce_width_end"]
        points[3].radius = 0.25 + 0.75 * geometry["reduce_width_end"]
        points[4].radius = 0.00 + 1.00 * geometry["reduce_width_end"]
        new_width = width * geometry["reduce_width_begin"] * geometry["reduce_width_end"]

        bpy.ops.object.mode_set(mode='OBJECT')
        curve.select_set(True)
        bpy.ops.object.convert(target='MESH')
        if (recursion_depth > 0):
            bpy.ops.object.particle_system_add()
            leafParticles = bpy.context.object.particle_systems.active
            leafParticles.name = "leavesSystem"
            leafParticles.settings.type = "HAIR"
            leafParticles.settings.count = 10 * (self.max_recursion_depth - recursion_depth + 1)
            leafParticles.settings.render_type = 'OBJECT'
            leafParticles.settings.instance_object = bpy.data.objects["leaf"]
            leafParticles.settings.size_random = 0.5
            leafParticles.settings.use_advanced_hair = True
            leafParticles.settings.rotation_mode = 'NOR_TAN'
            leafParticles.settings.use_rotations = True
            leafParticles.settings.rotation_factor_random = 0.2
            leafParticles.settings.particle_size = 0.1

        ob = bpy.context.active_object

        # Get material
        mat = bpy.data.materials.get("Material")
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="Material")

        # Assign it to object
        if ob.data.materials:
            # assign to 1st material slot
            ob.data.materials[0] = mat
        else:
            # no slots
            ob.data.materials.append(mat)

                
        return new_width, new_angle, new_position


parameters = {
    "start": "s",
    "stop": ["t"],
    "initial_width": [0.18, 0.22],
    "max_recursion_depth": 14,

    "grammar" : [
        {
            "input": "s",
            "output": [["a"]],
            "likelihood": [1],
        },
        {
            "input": "a",
            "output": [["a", "b1", "b1", "b1", "b1", "b2", "b2", "b2"], ["a", "b1", "b1", "b1", "b1", "b2", "b2"]],
            "likelihood": [1, 1]
        },
        {
            "input": "b1",
            "output": [["t"]],
            "likelihood": [1]
        },
        {
            "input": "b2",
            "output": [["c1", "c2"]],
            "likelihood": [1]
        },
        {
            "input": "c1",
            "output": [["t"]],
            "likelihood": [1]
        },
        {
            "input": "c2",
            "output": [["t"]],
            "likelihood": [1]
        }
    ],

    "geometries": [
        {
            "input": "s",
            "output": "a",
            "angle": [[0,1], [0,0], [0,360]],
            "length": [5,6],
            "reduce_length": 1.0,
            "reduce_width_begin": 1.0,
            "reduce_width_end": 0.95,
            "reduce_angle": [1.0, 1.0, 1.0],
            "curve": [0.18, 0.22]
        },
        {
            "input": "a",
            "output": "a",
            "angle": [[0,1], [0,0], [0,360]],
            "length": [1,2],
            "reduce_length": 0.9,
            "reduce_width_begin": 1.0,
            "reduce_width_end": 0.90,
            "reduce_angle": [1.0, 1.0, 1.0],
            "curve": [0.18, 0.22]
        },
        {
            "input": "a",
            "output": "b1",
            "angle": [[70,80], [0,0], [0,360]],
            "length": [2.5,3.5],
            "reduce_length": 0.95,
            "reduce_width_begin": 0.3,
            "reduce_width_end": 0.2,
            "reduce_angle": [0.90, 1.0, 1.0],
            "curve": [1.8, 2.2]
        },
        {
            "input": "a",
            "output": "b2",
            "angle": [[70,80], [0,0], [0,360]],
            "length": [1.5,2.5],
            "reduce_length": 0.95,
            "reduce_width_begin": 0.3,
            "reduce_width_end": 0.2,
            "reduce_angle": [0.90, 1.0, 1.0],
            "curve": [1.8, 2.2]
        },
        {
            "input": "b2",
            "output": "c1",
            "angle": [[2,-2], [2,-2], [15,30]],
            "length": [1,2],
            "reduce_length": 0.95,
            "reduce_width_begin": 1.0,
            "reduce_width_end": 0.5,
            "reduce_angle": [1.0, 1.0, 1.0],
            "curve": [1.8, 2.2]
        },
        {
            "input": "b2",
            "output": "c2",
            "angle": [[2,-2], [2,-2], [-15,-30]],
            "length": [1,2],
            "reduce_length": 0.95,
            "reduce_width_begin": 1.0,
            "reduce_width_end": 0.5,
            "reduce_angle": [1.0, 1.0, 1.0],
            "curve": [1.8, 2.2]
        }
    ]
}

bpy.ops.import_image.to_plane(
    files=[{
    "name":"path/to/texture/file.png", 
    "name":"path/to/texture/file.png"}],
    directory="path/to/texture/folder/", 
    align_axis='Z+'
)

tg = TreeGrammar(parameters)
tg.draw()
