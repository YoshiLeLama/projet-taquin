import pyray as pr
from collections import namedtuple
import taquin as tq

# types
PositionCase = namedtuple("PositionCase", ["l", "c"])

# constantes
TAILLE_GRILLE = 3
NOMBRE_BLOCS = TAILLE_GRILLE**2 - 1
NOMBRE_CASES = TAILLE_GRILLE**2
POSITIONS = [PositionCase(-1., -1.), PositionCase(0., -1), PositionCase(1., -1.),
             PositionCase(-1., 0.), PositionCase(0., 0.), PositionCase(1., 0.),
             PositionCase(-1., 1.), PositionCase(0., 1.), PositionCase(1., 1.)]
DUREE_ANIMATION = 0.5

# variables globales
camera = pr.Camera3D([0., 16.0, 5.0], [0.0, 0.0, 0.0],
                     [0.0, 1.0, 0.0], 45.0, 0)
font = None
num_textures = []
blocks_models = []
grille = []
move_north = False
move_south = False
move_west = False
move_east = False
positions = POSITIONS[:]

total_t = 0
animating = False
bloc_depart = PositionCase(0., 0.)
bloc_arrivee = PositionCase(0., 0.)


def init():
    global camera, font, num_textures, blocks_models, grille
    pr.init_window(800, 450, "Taquin")
    pr.set_window_state(pr.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    pr.set_window_min_size(800, 450)
    pr.set_target_fps(60)

    camera = pr.Camera3D([0., 16.0, 5.0], [0.0, 0.0, 0.0], [
                         0.0, 1.0, 0.0], 45.0, 0)
    pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

    font = pr.load_font_ex("resources/font/JetBrainsMono.ttf", 200, None, 0)

    for i in range(0, NOMBRE_BLOCS):
        render_tex = pr.load_render_texture(200, 200)
        pr.begin_texture_mode(render_tex)
        pr.clear_background(pr.VIOLET)
        pr.draw_text_ex(font, str(i), pr.Vector2(
            int(render_tex.texture.width / 4), 10), 200, 1., pr.WHITE)
        pr.end_texture_mode()
        img = pr.load_image_from_texture(render_tex.texture)
        pr.unload_render_texture(render_tex)
        num_textures.append(pr.load_texture_from_image(img))

    for i in range(0, NOMBRE_BLOCS):
        mesh = pr.gen_mesh_cube(2., 2., 2.)
        model = pr.load_model_from_mesh(mesh)

        model.materials[0].maps[pr.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = num_textures[i]

        blocks_models.append(model)

    for i in range(0, NOMBRE_BLOCS):
        grille.append(i)
    grille.append(-1)


def get_case(grille, l, c):
    return grille[l * TAILLE_GRILLE + c]


def set_case(grille, l, c, valeur):
    grille[l * TAILLE_GRILLE + c] = valeur


def swap_cases(grille, l_1, c_1, l_2, c_2):
    val_1 = get_case(grille, l_1, c_1)
    val_2 = get_case(grille, l_2, c_2)
    set_case(grille, l_2, c_2, val_1)
    set_case(grille, l_1, c_1, val_2)


def get_position_valeur(grille: list[int], valeur):
    index = grille.index(valeur)
    return PositionCase(index // TAILLE_GRILLE, index % TAILLE_GRILLE)


def animate_bloc(t: float, depart: PositionCase, arrivee: PositionCase):
    global total_t, positions, animating, DUREE_ANIMATION
    total_t += t
    if total_t >= DUREE_ANIMATION:
        positions[arrivee.l * TAILLE_GRILLE +
                  arrivee.c] = POSITIONS[arrivee.l * TAILLE_GRILLE + arrivee.c]
        animating = False
        total_t = 0.0
        return
    factor = (total_t * total_t * (3.0 - 2.0 * total_t)) / DUREE_ANIMATION
    pos_depart = POSITIONS[depart.l * TAILLE_GRILLE + depart.c]
    pos_arrivee = POSITIONS[arrivee.l * TAILLE_GRILLE + arrivee.c]
    print(pos_depart, pos_arrivee, factor)
    positions[arrivee.l * TAILLE_GRILLE + arrivee.c] = (pos_depart[0] + (pos_arrivee[0] - pos_depart[0]) * factor,
                                                        pos_depart[1] + (pos_arrivee[1] - pos_depart[1]) * factor)
    # print(arrivee.l * TAILLE_GRILLE + arrivee.c, positions[arrivee.l * TAILLE_GRILLE + arrivee.c], grille)


def handle_input():
    global move_north, move_south, move_west, move_east, animating, bloc_depart, bloc_arrivee

    if pr.is_key_up(pr.KeyboardKey.KEY_UP):
        move_north = False
    if pr.is_key_up(pr.KeyboardKey.KEY_DOWN):
        move_south = False
    if pr.is_key_up(pr.KeyboardKey.KEY_LEFT):
        move_west = False
    if pr.is_key_up(pr.KeyboardKey.KEY_RIGHT):
        move_east = False

    if animating:
        return

    case_vide = get_position_valeur(grille, -1)
    nouvelle_pos = case_vide

    if not move_north and pr.is_key_down(pr.KeyboardKey.KEY_UP):
        move_north = True
        if case_vide.l != TAILLE_GRILLE - 1:
            nouvelle_pos = PositionCase(case_vide.l + 1, case_vide.c)
    elif not move_south and pr.is_key_down(pr.KeyboardKey.KEY_DOWN):
        move_south = True
        if case_vide.l != 0:
            nouvelle_pos = PositionCase(case_vide.l - 1, case_vide.c)
    elif not move_west and pr.is_key_down(pr.KeyboardKey.KEY_LEFT):
        move_west = True
        if case_vide.c != TAILLE_GRILLE - 1:
            nouvelle_pos = PositionCase(case_vide.l, case_vide.c + 1)
    elif not move_east and pr.is_key_down(pr.KeyboardKey.KEY_RIGHT):
        move_east = True
        if case_vide.c != 0:
            nouvelle_pos = PositionCase(case_vide.l, case_vide.c - 1)

    if case_vide != nouvelle_pos:
        swap_cases(grille, case_vide.l, case_vide.c,
                   nouvelle_pos.l, nouvelle_pos.c)
        animating = True
        bloc_depart = nouvelle_pos
        bloc_arrivee = case_vide
        print(bloc_depart, bloc_arrivee)

# grille = tq.generer_grille_aleatoire(True)


def run():
    global animating, camera

    while not pr.window_should_close():
        pr.update_camera(camera)

        handle_input()
        if animating:
            animate_bloc(pr.get_frame_time(), bloc_depart, bloc_arrivee)

        pr.get_frame_time()

        pr.begin_drawing()
        pr.clear_background(pr.Color(250, 250, 250, 255))
        pr.begin_mode_3d(camera)
        pr.draw_grid(20, 1.0)

        for i in range(0, NOMBRE_CASES):
            val = grille[i]
            if val != -1:
                pr.draw_model(blocks_models[val], pr.Vector3(
                    positions[i][0] * 2., 1., positions[i][1] * 2), 0.9, pr.WHITE)
        pr.end_mode_3d()

        is_solved = True
        for i in range(0, NOMBRE_BLOCS):
            if grille[i] != i:
                is_solved = False

        if is_solved and not animating:
            pr.draw_text("Résolu", 10, 10, 30, pr.GREEN)
        else:
            pr.draw_text("Non résolu", 10, 10, 30, pr.RED)
        pr.end_drawing()
    pr.close_window()

if __name__ == '__main__':
    init()

    run()