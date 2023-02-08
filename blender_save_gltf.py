import bpy
import argparse
import mathutils
from math import radians


def loadInfo(info_name, geo_name):
    armature = bpy.data.armatures.new("armature")
    rigged_model = bpy.data.objects.new("rigged_model", armature)

    bpy.context.collection.objects.link(rigged_model)
    bpy.context.view_layer.objects.active = rigged_model
    bpy.ops.object.mode_set(mode='EDIT')

    f_info = open(info_name, 'r')
    joint_pos = {}
    joint_hier = {}
    joint_skin = []
    for line in f_info:
        word = line.split()
        if word[0] == 'joints':
            joint_pos[word[1]] = [
                float(word[2]),  float(word[3]), float(word[4])]
        if word[0] == 'root':
            root_pos = joint_pos[word[1]]
            root_name = word[1]

        if word[0] == 'hier':
            if word[1] not in joint_hier.keys():
                joint_hier[word[1]] = [word[2]]
            else:
                joint_hier[word[1]].append(word[2])
        if word[0] == 'skin':
            skin_item = word[1:]
            joint_skin.append(skin_item)
    f_info.close()

    print(joint_hier)

    current_mesh = bpy.context.selected_objects[0]

    this_level = [root_name]
    while this_level:
        next_level = []
        for node in this_level:
            print(f'Looking at {node}')
            pos = joint_pos[node]
            bone = armature.edit_bones.new(node)
            bone.head.x, bone.head.y, bone.head.z = pos[0], pos[1], pos[2]

            # if bone.name not in current_mesh.vertex_groups:
            #    current_mesh.vertex_groups.new(name=bone.name)

            has_parent = None
            is_child = False
            is_parent = node in joint_hier.keys()

            for parent, children in joint_hier.items():
                if node in children:
                    is_child = True
                    has_parent = parent
                    bone.parent = armature.edit_bones[parent]
                    if bone.parent.tail == bone.head:
                        bone.use_connect = True
                    # offset = bone.head - bone.parent.head
                    # bone.tail = bone.head + offset / 2
                    break

            if is_parent:
                x_distance = [abs(joint_pos[c][0] - pos[0])
                              for c in joint_hier[node]]

                print(x_distance)
                nearest_child_idx = x_distance.index(min(x_distance))
                nearest_child_pos = joint_pos[joint_hier[node]
                                              [nearest_child_idx]]

                bone.tail.x, bone.tail.y, bone.tail.z = nearest_child_pos[
                    0], nearest_child_pos[1], nearest_child_pos[2]

            elif bone.parent:
                offset = bone.head - bone.parent.head
                bone.tail = bone.head + offset / 2
            elif not is_child:
                # This node not is neither a parent nor a child
                bone.tail.x, bone.tail.y, bone.tail.z = pos[0], pos[1], pos[2]
                bone.tail.y += 0.1

            if is_parent:
                for c_node in joint_hier[node]:
                    next_level.append(c_node)

        this_level = next_level

    print(joint_skin)
    bpy.ops.object.mode_set(mode='POSE')
    # for v_skin in joint_skin:
    #    v_idx = int(v_skin.pop(0))
    #
    #    for i in range(0, len(v_skin), 2):
    #        current_mesh.vertex_groups[v_skin[i]].add([v_idx], float(v_skin[i + 1]), 'REPLACE')

    # rigged_model.matrix_world = current_mesh.matrix_world
    # rigged_model.matrix_world.translation = mathutils.Vector()
    rigged_model.location.xyz = 0
    # rigged_model.rotation_euler.x = radians(90)
    mod = current_mesh.modifiers.new('rignet', 'ARMATURE')
    mod.object = rigged_model
    bpy.ops.object.editmode_toggle()
    bpy.context.view_layer.objects.active = current_mesh
    # rigged_model.select_set(False)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.editmode_toggle()
    bpy.context.view_layer.objects.active = rigged_model
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    # disconnect bones
    armature = bpy.context.active_object
    print(armature.data.edit_bones)
    for bone_name, bone in armature.data.edit_bones.items():
        bone.use_connect = False

    # reset bones rotation
    for bone_name, bone in armature.data.edit_bones.items():
        bone.roll = 0
        bone.tail = bone.head + mathutils.Vector((0, bone.length, 0))
        bone.roll = 0

    # for bone_name, bone in armature.data.edit_bones.items():
    #     old_head = bone.head.copy()
    #     R = mathutils.Matrix.Rotation(radians(90), 4, bone.x_axis.normalized())
    #     bone.transform(R)
    #     offset_vec = -(bone.head - old_head)
    #     bone.head += offset_vec
    #     bone.tail += offset_vec

    # armature.world_matrix.translation

    return root_name, joint_pos


def getMeshOrigin():
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

    # for geo in geometries:
    #     if 'ShapeOrig' in geo:
    #         '''
    #         we can also use cmds.ls(geo, l=True)[0].split("|")[0]
    #         to get the upper level node name, but stick on this way for now
    #         '''
    #         geo_name = geo.replace('ShapeOrig', '')
    #         geo_list.append(geo_name)
    # if not geo_list:
    #     geo_list = cmds.ls(type='surfaceShape')
    return bpy.context.selected_objects[0]


def get_args():
    parser = argparse.ArgumentParser()

    # get all script args
    _, all_arguments = parser.parse_known_args()
    double_dash_index = all_arguments.index('--')
    script_args = all_arguments[double_dash_index + 1:]

    # add parser rules
    parser.add_argument('-i', '--model', help="OBJ file")
    parser.add_argument('-r', '--rig_file', help="rig text-file")
    parser.add_argument('-o', '--output', help="save GLTF")
    parsed_script_args, _ = parser.parse_known_args(script_args)
    return parsed_script_args


if __name__ == '__main__':
    model_id = "smith"
    print(model_id)
    obj_name = 'quick_start/{:s}_ori.obj'.format(model_id)
    info_name = 'quick_start/{:s}_ori_rig.txt'.format(model_id)
    out_name = 'quick_start/{:s}.gltf'.format(model_id)

    bpy.ops.object.delete({"selected_objects": [bpy.data.objects['Cube']]})

    args = get_args()

    # import obj
    bpy.ops.import_scene.obj(filepath=args.model)
    # cmds.file(new=True,force=True)
    # cmds.file(obj_name, o=True)

    mesh = getMeshOrigin()
    print(mesh.matrix_world)
    mesh.rotation_euler = (mathutils.Euler((0, 0, 0)))
    mesh.location.xyz = 0

    # import info
    root_name, _ = loadInfo(args.rig_file, mesh)

    # export fbx
    bpy.ops.export_scene.gltf(filepath=args.output)
