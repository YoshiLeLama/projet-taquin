import copy
from enum import Enum
import math
import random
import threading
import time
import pyray as pr
from collections import namedtuple
import taquin as tq

# types
PositionCase = namedtuple("PositionCase", ["l", "c"])


class State(Enum):
    INIT = 0
    TITLE_SCREEN = 1
    SETTINGS = 2
    GAME = 3
    RENDER_SOLVING = 4
    SOLVING_LOADING = 5


# constantes
TAILLE_GRILLE = 3
NOMBRE_BLOCS = TAILLE_GRILLE**2 - 1
NOMBRE_CASES = TAILLE_GRILLE**2
POSITIONS = [PositionCase(-1., -1.), PositionCase(0., -1), PositionCase(1., -1.),
             PositionCase(-1., 0.), PositionCase(0., 0.), PositionCase(1., 0.),
             PositionCase(-1., 1.), PositionCase(0., 1.), PositionCase(1., 1.)]
DUREE_ANIMATION = 0.5
BASE_CAMERA_POS = [0., 16.0, 5.0]

# variables globales
camera: pr.Camera3D
font = None
num_textures = []
blocks_models = []
grille = []
state = State.TITLE_SCREEN
last_state = State.TITLE_SCREEN

move_north = False
move_south = False
move_west = False
move_east = False
positions = POSITIONS[:]

nombre_deplacements = 0
indice = 0
solution: tq.Etat | None
deplacements: list[tq.Card] = []

total_t = 0
animating = False
bloc_depart = PositionCase(0., 0.)
bloc_arrivee = PositionCase(0., 0.)

resolve_button: pr.Texture
play_button: pr.Texture
settings_button: pr.Texture
reload_texture: pr.Texture


def init():
    global camera, font, num_textures, blocks_models, grille, bounding_box
    pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT)

    pr.init_window(800, 450, "Taquin")
    pr.set_window_state(pr.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    pr.set_window_min_size(800, 450)
    pr.set_target_fps(60)

    camera = pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                     [0.0, 1.0, 0.0], 45.0, 0)
    pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

    font = pr.load_font_ex("resources/font/JetBrainsMono.ttf", 200, None, 0)

    global settings_button, play_button, resolve_button, reload_texture
    resolve_button = pr.load_texture('resources/image/idea.png')
    play_button = pr.load_texture('resources/image/play.png')
    settings_button = pr.load_texture('resources/image/setting.png')
    reload_texture = pr.load_texture('resources/image/reload.png')

    for i in range(0, NOMBRE_BLOCS):
        render_tex = pr.load_render_texture(200, 200)
        pr.begin_texture_mode(render_tex)
        pr.clear_background(pr.Color(
            int(0 + (i / NOMBRE_BLOCS) * 155), 0, int(255 - (i / NOMBRE_BLOCS) * 155), 255))
        text_size = pr.measure_text_ex(font, str(i), 200, 1.)
        pr.draw_text_ex(font, str(i), pr.Vector2(
            int((render_tex.texture.width - text_size.x) / 2), int((render_tex.texture.height - text_size.y) / 2)), 200, 1., pr.WHITE)
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
    positions[arrivee.l * TAILLE_GRILLE + arrivee.c] = (pos_depart[0] + (pos_arrivee[0] - pos_depart[0]) * factor,
                                                        pos_depart[1] + (pos_arrivee[1] - pos_depart[1]) * factor)


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
    nouvelle_pos_vide = case_vide

    if not move_north and pr.is_key_down(pr.KeyboardKey.KEY_UP):
        move_north = True
        if case_vide.l != TAILLE_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.l + 1, case_vide.c)
    elif not move_south and pr.is_key_down(pr.KeyboardKey.KEY_DOWN):
        move_south = True
        if case_vide.l != 0:
            nouvelle_pos_vide = PositionCase(case_vide.l - 1, case_vide.c)
    elif not move_west and pr.is_key_down(pr.KeyboardKey.KEY_LEFT):
        move_west = True
        if case_vide.c != TAILLE_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c + 1)
    elif not move_east and pr.is_key_down(pr.KeyboardKey.KEY_RIGHT):
        move_east = True
        if case_vide.c != 0:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c - 1)

    if case_vide != nouvelle_pos_vide:
        swap_cases(grille, case_vide.l, case_vide.c,
                   nouvelle_pos_vide.l, nouvelle_pos_vide.c)
        animating = True
        bloc_depart = nouvelle_pos_vide
        bloc_arrivee = case_vide


def process_move(grille, deplacements, indice, nombre_deplacements):
    global animating, bloc_depart, bloc_arrivee

    if animating:
        return indice, nombre_deplacements

    case_vide = get_position_valeur(grille, -1)
    nouvelle_pos_vide = case_vide

    deplacement = deplacements[indice]

    if deplacement == tq.Card.N:
        if case_vide.l == 0:
            nouvelle_pos_vide = PositionCase(case_vide.l + 1, case_vide.c)
            deplacements[indice] = tq.Card.S
        else:
            nouvelle_pos_vide = PositionCase(case_vide.l - 1, case_vide.c)
            indice += 1
    elif deplacement == tq.Card.S:
        if case_vide.l == TAILLE_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.l - 1, case_vide.c)
            deplacements[indice] = tq.Card.N
        else:
            nouvelle_pos_vide = PositionCase(case_vide.l + 1, case_vide.c)
            indice += 1
    elif deplacement == tq.Card.O:
        if case_vide.c == 0:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c + 1)
            deplacements[indice] = tq.Card.E
        else:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c - 1)
            indice += 1
    elif deplacement == tq.Card.E:
        if case_vide.c == TAILLE_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c - 1)
            deplacements[indice] = tq.Card.O
        else:
            nouvelle_pos_vide = PositionCase(case_vide.l, case_vide.c + 1)
            indice += 1

    swap_cases(grille, case_vide.l, case_vide.c,
               nouvelle_pos_vide.l, nouvelle_pos_vide.c)
    nombre_deplacements += 1
    animating = True
    bloc_depart = nouvelle_pos_vide
    bloc_arrivee = case_vide

    return indice, nombre_deplacements

def draw_back_button():
    bg_color = pr.Color(50, 75, 255, 255)
    text_width = pr.measure_text("Retour", 30)
    if pr.check_collision_point_rec(pr.get_mouse_position(), pr.Rectangle(10, pr.get_render_height() - 40, text_width, 30)):
        bg_color = pr.Color(50, 125, 255, 255)
        if pr.is_mouse_button_down(pr.MouseButton.MOUSE_BUTTON_LEFT):
            global state
            state = State.TITLE_SCREEN
    pr.draw_rectangle(10, pr.get_render_height() -
                      40, text_width, 30, bg_color)
    pr.draw_text("Retour", 10, pr.get_render_height() - 40, 30, pr.BLACK)

def render_solving():
    global animating, camera, nombre_deplacements, indice, deplacements

    pr.update_camera(camera)
    i = indice

    if indice != len(deplacements):
        indice, nombre_deplacements = process_move(
            grille, deplacements, indice, nombre_deplacements)
    if animating:
        animate_bloc(pr.get_frame_time(), bloc_depart, bloc_arrivee)

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

    pr.draw_text("Nombre de mouvements : " + str(nombre_deplacements),
                 pr.get_screen_width() - pr.measure_text("Nombre de mouvements : " +
                                                         str(nombre_deplacements), 30) - 10,
                 10, 30, pr.BLACK)
    
    pr.draw_text(str(pr.get_fps()), 10, 50, 30, pr.BLACK)

    if is_solved and not animating:
        pr.draw_text("Résolu", 10, 10, 30, pr.GREEN)
    else:
        pr.draw_text("Non résolu", 10, 10, 30, pr.RED)

    draw_back_button()

    print(state)

    pr.end_drawing()


def render_game():
    global camera, grille, animating
    pr.update_camera(camera)

    handle_input()
    if animating:
        animate_bloc(pr.get_frame_time(), bloc_depart, bloc_arrivee)

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

    draw_back_button()

    pr.end_drawing()


def get_card_from_number(value):
    if value == 0:
        return tq.Card.N
    elif value == 1:
        return tq.Card.S
    elif value == 2:
        return tq.Card.O
    else:
        return tq.Card.E


def render_title_screen():
    global camera, grille, nombre_deplacements
    pr.update_camera(camera)

    process_move(grille, [get_card_from_number(
        random.randint(0, 3))], 0, nombre_deplacements)
    if animating:
        animate_bloc(pr.get_frame_time(), bloc_depart, bloc_arrivee)

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

    new_state = State.TITLE_SCREEN

    button_size = 100
    button_scale = button_size / play_button.width

    bg_color = pr.Color(50, 75, 255, 255)
    button_pos = pr.Vector2(int(pr.get_screen_width(
    ) / 2 - button_size * 1.5), int(pr.get_screen_height() - 200))
    if pr.check_collision_point_rec(pr.get_mouse_position(), pr.Rectangle(button_pos.x, button_pos.y, button_scale * play_button.width, button_scale * play_button.width)):
        bg_color = pr.Color(50, 125, 255, 255)
        new_state = State.GAME
    pr.draw_circle(int(button_pos.x + button_size / 2),
                   int(button_pos.y + button_size / 2), button_size / 2, bg_color)
    pr.draw_texture_ex(play_button, button_pos, 0., button_scale, pr.WHITE)

    bg_color = pr.Color(50, 75, 255, 255)
    button_pos = pr.Vector2(int(pr.get_screen_width(
    ) / 2 + button_size / 2), int(pr.get_screen_height() - 200))
    if pr.check_collision_point_rec(pr.get_mouse_position(), pr.Rectangle(button_pos.x, button_pos.y, button_scale * play_button.width, button_scale * play_button.width)):
        bg_color = pr.Color(50, 125, 255, 255)
        new_state = State.SOLVING_LOADING
    pr.draw_circle(int(button_pos.x + button_size / 2),
                   int(button_pos.y + button_size / 2), button_size / 2, bg_color)
    pr.draw_texture_ex(resolve_button, button_pos, 0., button_scale, pr.WHITE)

    bg_color = pr.Color(50, 75, 255, 255)
    button_pos = pr.Vector2(int(pr.get_screen_width(
    ) - button_size * 1.5), int(pr.get_screen_height() - button_size * 1.5))
    if pr.check_collision_point_rec(pr.get_mouse_position(), pr.Rectangle(button_pos.x, button_pos.y, button_scale * play_button.width, button_scale * play_button.width)):
        bg_color = pr.Color(50, 125, 255, 255)
        new_state = State.SETTINGS
    pr.draw_circle(int(button_pos.x + button_size / 2),
                   int(button_pos.y + button_size / 2), button_size / 2, bg_color)
    pr.draw_texture_ex(settings_button, button_pos, 0., button_scale, pr.WHITE)

    title_width = pr.measure_text("Taquin 3D 2023", 70)
    pr.draw_text("Taquin 3D 2023", int((pr.get_screen_width() - title_width) / 2), 50, 70, pr.Color(150, 50, 50, 255))

    pr.end_drawing()

    global state
    if pr.is_mouse_button_down(pr.MouseButton.MOUSE_BUTTON_LEFT):
        state = new_state
    else:
        state = State.TITLE_SCREEN


def render_loading_screen():
    pr.update_camera(camera)
    pr.begin_drawing()
    pr.clear_background(pr.GRAY)
    reload_icon_size = 50
    pr.draw_texture_pro(reload_texture,
                        pr.Rectangle(0, 0, reload_texture.width,
                                     reload_texture.height),
                        pr.Rectangle(int(pr.get_screen_width() / 2),
                                     int(pr.get_screen_height() / 2),
                                     reload_icon_size, reload_icon_size),
                        pr.Vector2(reload_icon_size / 2, reload_icon_size / 2),
                        pr.get_time() % 30. * 360., pr.WHITE)
    pr.begin_mode_3d(camera)
    pr.end_mode_3d()

    pr.end_drawing()


def load_solution():
    global deplacements
    solution = tq.astar(grille)
    if solution is not None:
        deplacements = solution.liste_deplacement

def base_camera():
    return pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                     [0.0, 1.0, 0.0], 45.0, 0)


def run():
    global animating, camera, state, last_state, grille, positions


    random.seed()

    last_state = State.INIT
    state = State.TITLE_SCREEN

    loading_thread: threading.Thread = threading.Thread()

    while not pr.window_should_close():
        if state == State.TITLE_SCREEN:
            if state != last_state:
                camera = base_camera()
                camera.position.z = 18.
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_ORBITAL)

            last_state = state
            render_title_screen()
        elif state == State.SETTINGS:
            ...
        elif state == State.GAME:
            if state != last_state:
                camera = base_camera()
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

                grille = tq.generer_grille_aleatoire(True)
                positions = POSITIONS[:]
                animating = False

            last_state = state
            render_game()
        elif state == State.RENDER_SOLVING:
            if state != last_state:
                camera = base_camera()
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)
                positions = POSITIONS[:]
                animating = False

            last_state = state
            render_solving()
        elif state == State.SOLVING_LOADING:
            if state != last_state:
                global indice, nombre_deplacements, deplacements
                indice = 0
                nombre_deplacements = 0
                grille = tq.generer_grille_aleatoire(True)
                loading_thread = threading.Thread(target=load_solution)
                loading_thread.start()

            last_state = state
            render_loading_screen()

            if not loading_thread.is_alive():
                state = State.RENDER_SOLVING

    pr.close_window()


if __name__ == '__main__':
    init()
    # render_solving(plateau, deplacements)
    run()
