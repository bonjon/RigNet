import bpy
import argparse
import mathutils
from math import radians
import re

# blender -P blender_save_gltf.py -- -i quick_start/result_ori.obj -r quick_start/result_ori_rig.txt -o quick_start/result.glb


def removeDuplicateBones(joint_hier, joint_pos):
    new_hier = joint_hier.copy()
    new_pos = joint_pos.copy()

    default_duplicated = {}
    for pos in joint_pos:
        match: re.Match = re.search(r"joint_(\d+)_dup_(\d+)", pos)
        if match is not None:
            id = match.groups()[0]
            dup = match.groups()[1]
            joint = f'joint_{id}'

            if joint not in default_duplicated:
                default_duplicated[joint] = set()

            default_duplicated[joint].add(
                f'joint_{id}_dup_{dup}')

        match: re.Match = re.search(r"root_dup_(\d+)", pos)
        if match is not None:
            dup = match.groups()[0]

            if 'root' not in default_duplicated:
                default_duplicated['root'] = set()

            default_duplicated['root'].add(
                f'root_dup_{dup}')

    for parent, duplicated_joints in default_duplicated.items():
        # root, [root_dup_0, root_dup_1, root_dup_2]
        for child in duplicated_joints:
            print(f"{parent} -> {child}")
            if child in new_hier:
                new_hier[parent].remove(child)
                new_hier[parent] += new_hier[child]
                new_hier.pop(child)
                new_pos.pop(child)

    # print("AFTER REMOVING DUPs", new_hier)

    # positions = [(j, pos) for j, pos in new_pos.items()]
    # positions = sorted(positions, key=lambda x: x[1])
    #
    # duplicated_joints = {}
    #
    # print("DUPLICATED JOINTS:", duplicated_joints)

    # print("OLD HIERARCHY", joint_hier)
    #
    # def fix_duplicated_roots(parent, joint):
    #     ending_childs = set()
    #     print(f"Watching {parent} -> {joint}")
    #     if joint in duplicated_joints:
    #         for child in duplicated_joints[joint]:
    #             ending_childs |= fix_duplicated_roots(joint, child)
    #             duplicated_joints.pop(joint)
    #     else:
    #         ending_childs.add(joint)
    #
    #     return ending_childs
    #
    # for parent, children in duplicated_joints.copy().items():
    #     print(f"FIXING DUPLICATES FOR {parent} ({children}):")
    #     res = set()
    #     for child in children:
    #         res |= fix_duplicated_roots(parent, child)
    #
    #     print(f"\t {parent}: {res}")
    #     if parent in duplicated_joints:
    #         duplicated_joints[parent] = res
    #
    # print("FINAL DUPLICATE SET", duplicated_joints)
    #
    # for root, children in duplicated_joints.items():
    #     for child in children:
    #         if root not in new_hier:
    #             new_hier[root] = []
    #
    #         if child in new_hier:
    #             new_hier[root] += new_hier[child]
    #             new_hier.pop(child)
    #             new_pos.pop(child)
    #
    #         if child in new_hier[root]:
    #             new_hier[root].remove(child)
    #
    #         for parent, other_childs in new_hier.items():
    #             if child in other_childs:
    #                 other_childs.remove(child)

    for parent, children in new_hier.copy().items():
        if len(children) == 0:
            new_hier.pop(parent)

    print("NEW HIERARCHY", new_hier)

    return new_hier, new_pos


def adjustBones(joint_hier, joint_pos):
    new_pos = joint_pos.copy()
    new_hier = joint_hier.copy()
    limbs_roots = {}
    labeled_leaves = {}

    leaves = [n for n in joint_pos.keys() if n not in joint_hier]
    print(f'Leaves: {leaves}\npos: \t{[joint_pos[l] for l in leaves]}')

    highest_x, highest_y = (0, 0)
    lowest_x, lowest_y, second_lowest_y = (0, 0, 0)

    labeled_leaves["right_arm_0"] = []
    labeled_leaves["left_arm_0"] = []
    labeled_leaves["head_0"] = []
    labeled_leaves["right_leg_0"] = []
    labeled_leaves["left_leg_0"] = []

    for leaf in leaves:
        pos = joint_pos[leaf]

        if pos[0] > highest_x:
            labeled_leaves["left_arm_0"] = leaf
            highest_x = pos[0]
        if pos[0] < lowest_x:
            labeled_leaves["right_arm_0"] = leaf
            lowest_x = pos[0]
        if pos[1] > highest_y:
            labeled_leaves["head_0"] = leaf
            highest_y = pos[1]
        if pos[1] < lowest_y and pos[0] > 0:
            labeled_leaves["left_leg_0"] = leaf
            lowest_y = pos[1]
        if pos[1] < second_lowest_y and pos[0] < 0:
            labeled_leaves["right_leg_0"] = leaf
            second_lowest_y = pos[1]

    inverted_labeled_leaves = {}

    for k, v in labeled_leaves.items():
        inverted_labeled_leaves[v] = k

    labeled_leaves = inverted_labeled_leaves

    print(f'Leaves: {labeled_leaves}')

    # here we find the limb "root" (the beginning of the limb)
    for parent, children in joint_hier.items():
        limb_root_candidate = children[0]
        candidate_parent = parent
        print(f'Inspecting {parent} -> {children}...')
        if len(children) == 1 and children[0] in labeled_leaves:
            while len(joint_hier[candidate_parent]) < 2:
                # print(
                #     f'\t{candidate_parent} -> {joint_hier[candidate_parent]}')
                for parent_it, children_it in joint_hier.items():
                    if candidate_parent in children_it:
                        print(f'Candidate parent: {candidate_parent}')
                        limb_root_candidate = candidate_parent
                        candidate_parent = parent_it
            limbs_roots[limb_root_candidate] = labeled_leaves[children[0]]

    # restructure the hierarchy
    print(f'Limb roots:\n \t {limbs_roots}')
    print(f'Limb children:\n\t {[joint_hier[r] for r in limbs_roots]}')
    for limb_root in limbs_roots:
        print(f'Limb root: {limb_root}')
        counter = 0
        pos = joint_pos[limb_root]
        old_name = limb_root
        new_name = limbs_roots[limb_root]

        while old_name in joint_hier:
            new_name = new_name[:-1]+str(counter)
            # il while controlla anche se è l'ultimo parent della catena
            new_pos[new_name] = joint_pos[old_name]
            new_pos.pop(old_name)
            print(f'{old_name} -> {new_name}: {joint_hier[old_name]}')
            if joint_hier[old_name][0] in joint_hier:
                new_hier[new_name] = [new_name[:-1]+(str(counter+1))]
            else:
                leaf_pos = joint_pos[joint_hier[old_name][0]]
                new_pos[new_name[:-1]+(str(counter+1))] = leaf_pos
                new_pos.pop(joint_hier[old_name][0])

                new_hier[new_name[:-1] +
                         str(counter)] = [new_name[:-1]+(str(counter+1))]

            counter += 1
            new_hier.pop(old_name)
            old_name = joint_hier[old_name][0]

        for parent, children in new_hier.items():
            if limb_root in children:
                children[children.index(limb_root)] = limbs_roots[limb_root]

    print(f'Resulted in:\n\t{new_pos}\n\t{new_hier}')
    return new_hier, new_pos


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

    joint_hier, joint_pos = removeDuplicateBones(joint_hier, joint_pos)
    joint_hier, joint_pos = adjustBones(joint_hier, joint_pos)

    current_mesh = bpy.context.selected_objects[0]

    this_level = [root_name]
    while this_level:
        next_level = []
        for node in this_level:
            print(f'Looking at {node}')
            pos = joint_pos[node]
            bone = armature.edit_bones.new(node)
            print(pos)
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

    bpy.ops.object.mode_set(mode='POSE')

    # rigged_model.matrix_world = current_mesh.matrix_world
    # rigged_model.matrix_world.translation = mathutils.Vector()
    # rigged_model.location.xyz = 0
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
    for bone_name, bone in armature.data.edit_bones.items():
        bone.use_connect = False

    # reset bones rotation
    for bone_name, bone in armature.data.edit_bones.items():
        bone.roll = 0
        bone.tail = bone.head - mathutils.Vector((0, bone.length, 0))
        bone.roll = 0

    return root_name, joint_pos


def getMeshOrigin():
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

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
    bpy.ops.object.delete({"selected_objects": [bpy.data.objects['Cube']]})

    args = get_args()

    # import obj
    bpy.ops.import_scene.obj(filepath=args.model)

    mesh = getMeshOrigin()
    mesh.rotation_euler = (mathutils.Euler((0, 0, 0)))
    mesh.location.xyz = 0

    # import info
    root_name, _ = loadInfo(args.rig_file, mesh)

    # export fbx
    bpy.ops.export_scene.gltf(filepath=args.output)
