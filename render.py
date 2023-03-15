import math
import random
import threading
from collections import namedtuple
from enum import Enum

import pyray as pr

import taquin as tq

# types
PositionCase = namedtuple("PositionCase", ["ligne", "colonne"])


class State(Enum):
    INIT = 0
    TITLE_SCREEN = 1
    SETTINGS = 2
    GAME = 3
    RENDER_SOLVING = 4
    SOLVING_LOADING = 5
    SOLVING_SETTINGS = 6


# constantes
POSITIONS = [PositionCase(-1., -1.), PositionCase(0., -1), PositionCase(1., -1.),
             PositionCase(-1., 0.), PositionCase(0., 0.), PositionCase(1., 0.),
             PositionCase(-1., 1.), PositionCase(0., 1.), PositionCase(1., 1.)]
BASE_CAMERA_POS = [0., 16.0, 5.0]
BUTTON_BG = pr.Color(50, 75, 255, 255)
BUTTON_BG_HOVERED = pr.Color(50, 125, 255, 255)

# variables globales
camera: pr.Camera3D
font = None
num_textures: list[pr.Texture] = []
num_textures_for_2d: list[pr.Texture] = []
blocks_models: list[pr.Model] = []
state = State.TITLE_SCREEN
last_state = State.TITLE_SCREEN

positions = POSITIONS[:]

grille_initiale: list[int] = []
grille_actuelle: list[int] = []
nombre_deplacements = 0
indice = 0
solution: tq.Etat | None
deplacements: list[tq.Card] = []
liste_deplacements_initiale: list[tq.Card] = []

duree_animation = 0.5
total_t = 0
animating = False
bloc_depart = PositionCase(0., 0.)
bloc_arrivee = PositionCase(0., 0.)

resolve_texture: pr.Texture
play_texture: pr.Texture
settings_texture: pr.Texture
reload_texture: pr.Texture


def init():
    global camera, font, num_textures, blocks_models, grille_actuelle
    pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT)

    pr.init_window(800, 450, "Taquin")
    pr.set_window_state(pr.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    pr.set_window_min_size(800, 450)
    pr.set_target_fps(60)

    camera = pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                         [0.0, 1.0, 0.0], 45.0, 0)
    pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

    font = pr.load_font_ex("resources/font/JetBrainsMono.ttf", 200, None, 0)

    global settings_texture, play_texture, resolve_texture, reload_texture
    resolve_texture = pr.load_texture('resources/image/idea.png')
    play_texture = pr.load_texture('resources/image/play.png')
    settings_texture = pr.load_texture('resources/image/setting.png')
    reload_texture = pr.load_texture('resources/image/reload.png')

    for i in range(0, tq.NOMBRE_TUILES):
        render_tex = pr.load_render_texture(200, 200)
        pr.begin_texture_mode(render_tex)
        pr.clear_background(
            pr.Color(int(0 + (i / tq.NOMBRE_TUILES) * 155), 0, int(255 - (i / tq.NOMBRE_TUILES) * 155), 255))
        text_size = pr.measure_text_ex(font, str(i), 200, 1.)
        pr.draw_text_ex(font, str(i), pr.Vector2(int((render_tex.texture.width - text_size.x) / 2),
                                                 int((render_tex.texture.height - text_size.y) / 2)),
                        200, 1., pr.WHITE)
        pr.end_texture_mode()
        img = pr.load_image_from_texture(render_tex.texture)
        num_textures.append(pr.load_texture_from_image(img))
        img = pr.load_image_from_texture(render_tex.texture)
        pr.image_flip_vertical(img)
        num_textures_for_2d.append(pr.load_texture_from_image(img))

        pr.unload_render_texture(render_tex)

    for i in range(0, tq.NOMBRE_TUILES):
        mesh = pr.gen_mesh_cube(2., 2., 2.)
        model = pr.load_model_from_mesh(mesh)

        model.materials[0].maps[pr.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = num_textures[i]

        blocks_models.append(model)

    for i in range(0, tq.NOMBRE_TUILES):
        grille_actuelle.append(i)
    grille_actuelle.append(-1)


def get_case(grille, ligne, colonne):
    return grille[ligne * tq.DIM_GRILLE + colonne]


def set_case(grille, ligne, colonne, valeur):
    grille[ligne * tq.DIM_GRILLE + colonne] = valeur


def swap_cases(grille, ligne_1, colonne_1, ligne_2, colonne_2):
    val_1 = get_case(grille, ligne_1, colonne_1)
    val_2 = get_case(grille, ligne_2, colonne_2)
    set_case(grille, ligne_2, colonne_2, val_1)
    set_case(grille, ligne_1, colonne_1, val_2)


def get_position_valeur(g: list[int], valeur):
    index = g.index(valeur)
    return PositionCase(index // tq.DIM_GRILLE, index % tq.DIM_GRILLE)


def reset_animation():
    global total_t, positions, animating
    total_t = 0
    positions = POSITIONS[:]
    animating = False


def animate_bloc(t: float, depart: PositionCase, arrivee: PositionCase):
    global total_t, positions, animating
    total_t += t
    if total_t >= duree_animation:
        positions[arrivee.ligne * tq.DIM_GRILLE +
                  arrivee.colonne] = POSITIONS[arrivee.ligne * tq.DIM_GRILLE + arrivee.colonne]
        animating = False
        total_t = 0.0
        return
    normal_time = total_t / duree_animation
    factor = (normal_time * normal_time * (3.0 - 2.0 * normal_time))
    pos_depart = POSITIONS[depart.ligne * tq.DIM_GRILLE + depart.colonne]
    pos_arrivee = POSITIONS[arrivee.ligne * tq.DIM_GRILLE + arrivee.colonne]
    positions[arrivee.ligne * tq.DIM_GRILLE + arrivee.colonne] = PositionCase(
        pos_depart.ligne + (pos_arrivee.ligne - pos_depart.ligne) * factor,
        pos_depart.colonne + (pos_arrivee.colonne - pos_depart.colonne) * factor)


def handle_input():
    global animating, bloc_depart, bloc_arrivee, nombre_deplacements

    if animating:
        return

    case_vide = get_position_valeur(grille_actuelle, -1)
    nouvelle_pos_vide = case_vide

    if pr.is_key_pressed(pr.KeyboardKey.KEY_UP):
        if case_vide.ligne != tq.DIM_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.ligne + 1, case_vide.colonne)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_DOWN):
        if case_vide.ligne != 0:
            nouvelle_pos_vide = PositionCase(case_vide.ligne - 1, case_vide.colonne)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_LEFT):
        if case_vide.colonne != tq.DIM_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne + 1)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_RIGHT):
        if case_vide.colonne != 0:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne - 1)

    if case_vide != nouvelle_pos_vide:
        swap_cases(grille_actuelle, case_vide.ligne, case_vide.colonne,
                   nouvelle_pos_vide.ligne, nouvelle_pos_vide.colonne)
        animating = True
        bloc_depart = nouvelle_pos_vide
        bloc_arrivee = case_vide
        nombre_deplacements += 1


def process_move():
    global animating, bloc_depart, bloc_arrivee, deplacements, nombre_deplacements, indice

    if animating:
        return

    case_vide = get_position_valeur(grille_actuelle, -1)
    nouvelle_pos_vide = case_vide

    deplacement = deplacements[indice]

    if deplacement == tq.Card.N:
        if case_vide.ligne == 0:
            nouvelle_pos_vide = PositionCase(case_vide.ligne + 1, case_vide.colonne)
            deplacements[indice] = tq.Card.S
        else:
            nouvelle_pos_vide = PositionCase(case_vide.ligne - 1, case_vide.colonne)
            indice += 1
    elif deplacement == tq.Card.S:
        if case_vide.ligne == tq.DIM_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.ligne - 1, case_vide.colonne)
            deplacements[indice] = tq.Card.N
        else:
            nouvelle_pos_vide = PositionCase(case_vide.ligne + 1, case_vide.colonne)
            indice += 1
    elif deplacement == tq.Card.O:
        if case_vide.colonne == 0:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne + 1)
            deplacements[indice] = tq.Card.E
        else:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne - 1)
            indice += 1
    elif deplacement == tq.Card.E:
        if case_vide.colonne == tq.DIM_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne - 1)
            deplacements[indice] = tq.Card.O
        else:
            nouvelle_pos_vide = PositionCase(case_vide.ligne, case_vide.colonne + 1)
            indice += 1

    swap_cases(grille_actuelle, case_vide.ligne, case_vide.colonne,
               nouvelle_pos_vide.ligne, nouvelle_pos_vide.colonne)
    nombre_deplacements += 1
    animating = True
    bloc_depart = nouvelle_pos_vide
    bloc_arrivee = case_vide


def draw_back_button(target_state: State):
    bg_color = pr.Color(50, 75, 255, 255)
    text_width = pr.measure_text("Retour", 30)
    if pr.check_collision_point_rec(pr.get_mouse_position(),
                                    pr.Rectangle(10, pr.get_render_height() - 40, text_width, 30)):
        bg_color = pr.Color(50, 125, 255, 255)
        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            global state
            state = target_state
    pr.draw_rectangle(8, pr.get_render_height() -
                      40, text_width + 4, 30, bg_color)
    pr.draw_text("Retour", 10, pr.get_render_height() - 40, 30, pr.BLACK)


def draw_reload_button(position: pr.Vector2, size: int):
    button_scale = size / reload_texture.width
    bg_color = BUTTON_BG

    if pr.check_collision_point_rec(pr.get_mouse_position(),
                                    pr.Rectangle(position.x, position.y, button_scale * play_texture.width,
                                                 button_scale * play_texture.width)):
        bg_color = BUTTON_BG_HOVERED

        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            if state == State.GAME:
                reload_game()
            elif state == State.RENDER_SOLVING:
                restart_solving()

    pr.draw_circle(int(position.x + size / 2),
                   int(position.y + size / 2), size / 2, bg_color)
    pr.draw_texture_ex(reload_texture, position, 0., button_scale, pr.WHITE)


def is_solved():
    for i in range(0, tq.NOMBRE_TUILES):
        if grille_actuelle[i] != i:
            return False
    return True


def render_grid():
    global animating
    if animating:
        animate_bloc(pr.get_frame_time(), bloc_depart, bloc_arrivee)

    pr.clear_background(pr.Color(250, 250, 250, 255))
    pr.begin_mode_3d(camera)
    pr.draw_grid(20, 1.0)

    for i in range(0, tq.NOMBRE_CASES):
        val = grille_actuelle[i]
        if val != -1:
            pr.draw_model(blocks_models[val], pr.Vector3(
                positions[i][0] * 2., 1., positions[i][1] * 2), 0.9, pr.WHITE)
    pr.end_mode_3d()


def render_solved_text():
    global grille_actuelle, animating
    if is_solved() and not animating:
        pr.draw_text("Résolu", 10, 10, 30, pr.GREEN)
    else:
        pr.draw_text("Non résolu", 10, 10, 30, pr.RED)


def restart_solving():
    global indice, nombre_deplacements, grille_actuelle, deplacements
    indice = 0
    nombre_deplacements = 0
    grille_actuelle = grille_initiale[:]
    deplacements = liste_deplacements_initiale[:]
    reset_animation()


def render_solving():
    global animating, camera, nombre_deplacements, indice, deplacements

    pr.update_camera(camera)

    if indice != len(deplacements):
        process_move()

    pr.begin_drawing()

    render_grid()

    draw_nombre_mouvements()

    pr.draw_text(str(pr.get_fps()), 10, 50, 30, pr.BLACK)

    button_size = 80
    draw_reload_button(pr.Vector2(pr.get_screen_width() - button_size - 10,
                                  pr.get_screen_height() - button_size - 10), button_size)

    render_solved_text()

    draw_back_button(State.SOLVING_SETTINGS)

    pr.end_drawing()


def draw_nombre_mouvements():
    global nombre_deplacements
    pr.draw_text("Nombre de mouvements : " + str(nombre_deplacements),
                 pr.get_screen_width() - pr.measure_text("Nombre de mouvements : " +
                                                         str(nombre_deplacements), 30) - 10,
                 10, 30, pr.BLACK)


def reload_game():
    global nombre_deplacements, grille_actuelle
    nombre_deplacements = 0
    grille_actuelle = tq.generer_grille_aleatoire(True)
    reset_animation()


def render_game():
    global camera, grille_actuelle, animating
    pr.update_camera(camera)

    pr.begin_drawing()

    render_grid()

    render_solved_text()

    draw_nombre_mouvements()

    draw_back_button(State.TITLE_SCREEN)

    button_size = 80
    draw_reload_button(pr.Vector2(pr.get_screen_width() - button_size - 10,
                                  pr.get_screen_height() - button_size - 10), button_size)

    pr.end_drawing()

    if not is_solved():
        handle_input()


def get_card_from_number(value):
    if value == 0:
        return tq.Card.N
    elif value == 1:
        return tq.Card.O
    elif value == 2:
        return tq.Card.S
    else:
        return tq.Card.E


def draw_state_switch_button(texture: pr.Texture, position: pr.Vector2, size: int, target_state: State):
    button_scale = size / texture.width
    bg_color = BUTTON_BG

    if pr.check_collision_point_rec(pr.get_mouse_position(),
                                    pr.Rectangle(position.x, position.y, button_scale * play_texture.width,
                                                 button_scale * play_texture.width)):
        bg_color = BUTTON_BG_HOVERED

        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            global state
            state = target_state

    pr.draw_circle(int(position.x + size / 2),
                   int(position.y + size / 2), size / 2, bg_color)
    pr.draw_texture_ex(texture, position, 0., button_scale, pr.WHITE)


def process_title_screen_moves():
    global deplacements, indice, nombre_deplacements
    deplacements = [get_card_from_number(random.randint(0, 3))]
    indice = 0
    process_move()


def render_title_screen():
    global camera
    pr.update_camera(camera)

    process_title_screen_moves()

    pr.begin_drawing()
    render_grid()

    button_size = 100

    draw_state_switch_button(play_texture, pr.Vector2(int(pr.get_screen_width() / 2 - button_size * 1.5),
                                                      int(pr.get_screen_height() - 200)),
                             button_size, State.GAME)

    draw_state_switch_button(resolve_texture, pr.Vector2(int(pr.get_screen_width() / 2 + button_size / 2),
                                                         int(pr.get_screen_height() - 200)),
                             button_size, State.SOLVING_SETTINGS)

    button_size = 70

    draw_state_switch_button(settings_texture, pr.Vector2(int(pr.get_screen_width() - button_size * 1.5),
                                                          int(pr.get_screen_height() - button_size * 1.5)),
                             button_size, State.SETTINGS)

    title_width = pr.measure_text("Taquin 3D 2023", 70)
    pr.draw_text("Taquin 3D 2023", int((pr.get_screen_width() - title_width) / 2), 50, 70, pr.Color(150, 50, 50, 255))

    pr.end_drawing()


def render_loading_screen():
    pr.update_camera(camera)
    pr.begin_drawing()
    pr.clear_background(pr.GRAY)
    pr.begin_mode_3d(camera)
    pr.end_mode_3d()
    reload_icon_size = 50
    pr.draw_texture_pro(reload_texture,
                        pr.Rectangle(0, 0, reload_texture.width,
                                     reload_texture.height),
                        pr.Rectangle(int(pr.get_screen_width() / 2),
                                     int(pr.get_screen_height() / 2),
                                     reload_icon_size, reload_icon_size),
                        pr.Vector2(reload_icon_size / 2, reload_icon_size / 2),
                        pr.get_time() % 30. * 360., pr.WHITE)

    pr.end_drawing()


SETTINGS_PANEL_MARGIN = 10


def render_settings():
    global duree_animation
    process_title_screen_moves()

    pr.begin_drawing()
    render_grid()

    pr.draw_rectangle(SETTINGS_PANEL_MARGIN, SETTINGS_PANEL_MARGIN,
                      pr.get_screen_width() - SETTINGS_PANEL_MARGIN * 2,
                      pr.get_render_height() - SETTINGS_PANEL_MARGIN * 2, pr.Color(255, 255, 255, 220))

    font_size = 30
    contenu = "Durée d'animation : "
    size = int(pr.measure_text(contenu, font_size))
    value = round(duree_animation, 1)
    position = pr.Vector2(pr.get_screen_width() / 2 - size,
                          SETTINGS_PANEL_MARGIN + 10)
    color = pr.BLACK

    if pr.check_collision_point_rec(pr.get_mouse_position(),
                                    pr.Rectangle(position.x, position.y,
                                                 size + pr.measure_text(str(value), font_size), font_size)):
        color = pr.GRAY
        if pr.get_mouse_wheel_move_v().y > 0:
            duree_animation = min(1.5, duree_animation + 0.1)
        elif pr.get_mouse_wheel_move_v().y < 0:
            duree_animation = max(0.2, duree_animation - 0.1)

    pr.draw_text(contenu + str(value),
                 int(position.x), int(position.y), font_size, color)

    draw_back_button(State.TITLE_SCREEN)
    pr.end_drawing()


case_selectionee = 0

selected_cases = [-1, -1]


def render_resolve_settings():
    pr.update_camera(camera)

    pr.begin_drawing()
    pr.clear_background(pr.Color(250, 250, 250, 255))

    text: str
    couleur: pr.Color
    soluble = tq.solvable(grille_actuelle)
    if soluble:
        text = "Résoluble"
        color = pr.GREEN
    else:
        text = "Impossible"
        color = pr.RED

    pr.draw_text(text, 10, 10, 30, color)

    taille_case = 100
    case_scale = taille_case / num_textures_for_2d[0].width

    hovered_case = -1

    global selected_cases
    for i in range(0, tq.NOMBRE_CASES):
        position = pr.Vector2(
            int(pr.get_screen_width() / 2 +
                taille_case * (i % tq.DIM_GRILLE - tq.DIM_GRILLE // 2 - 0.5)),
            int(pr.get_screen_height() / 2 +
                taille_case * (i // tq.DIM_GRILLE - tq.DIM_GRILLE // 2 - 0.5)))
        if grille_actuelle[i] != -1:
            pr.draw_texture_ex(num_textures_for_2d[grille_actuelle[i]],
                               position,
                               0,
                               case_scale,
                               pr.WHITE)

        if selected_cases[0] == i:
            pr.draw_rectangle_lines_ex(pr.Rectangle(int(position.x), int(position.y), taille_case, taille_case),
                                       5., pr.BLACK)

        if pr.check_collision_point_rec(pr.get_mouse_position(),
                                        pr.Rectangle(position.x, position.y,
                                                     taille_case,
                                                     taille_case)):
            hovered_case = grille_actuelle[i]
            if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
                if selected_cases[0] != -1:
                    selected_cases[1] = i
                else:
                    selected_cases[0] = i

    if selected_cases[0] != -1 and selected_cases[1] != -1:
        tq.swap(grille_actuelle, selected_cases[0], selected_cases[1])
        selected_cases = [-1, -1]

    button_size = 100
    button_position = pr.Vector2(pr.get_screen_width() - button_size - 10,
                                 pr.get_screen_height() - button_size - 10)
    if soluble:
        draw_state_switch_button(play_texture, button_position,
                                 button_size, State.SOLVING_LOADING)
    else:
        pr.draw_circle(int(button_position.x + button_size / 2), int(button_position.y + button_size / 2),
                       button_size / 2, pr.GRAY)
        pr.draw_texture_ex(play_texture, button_position, 0., button_size / play_texture.width,
                           pr.Color(255, 255, 255, 255))

    pr.draw_text("Set de poids " + str(tq.K), 10, pr.get_screen_height() - 100, 30, pr.BLACK)

    if hovered_case != -1:
        tooltip = "poids = " + str(tq.get_poids_tuile(tq.K, hovered_case))
        pr.draw_rectangle(int(pr.get_mouse_position().x + 18), int(pr.get_mouse_position().y),
                          pr.measure_text(tooltip, 20) + 4, 20, pr.BLACK)
        pr.draw_text(tooltip, int(pr.get_mouse_position().x + 20),
                     int(pr.get_mouse_position().y), 20,
                     pr.WHITE)

    if pr.get_mouse_wheel_move_v().y > 0:
        tq.set_weight_set(tq.K + 1)
    elif pr.get_mouse_wheel_move_v().y < 0:
        tq.set_weight_set(tq.K - 1)

    draw_back_button(State.TITLE_SCREEN)
    pr.end_drawing()


def load_solution():
    global deplacements, solution, liste_deplacements_initiale
    solution = tq.astar(grille_actuelle)
    if solution is not None:
        deplacements = solution.liste_deplacement
        liste_deplacements_initiale = deplacements[:]


def base_camera():
    return pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0], 45.0, 0)


def run():
    global animating, camera, state, last_state, grille_actuelle, grille_initiale, positions, indice
    global nombre_deplacements, deplacements

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
                grille_actuelle = tq.generer_grille_aleatoire()
                reset_animation()

            last_state = state
            render_title_screen()
        elif state == State.SETTINGS:
            if state != last_state:
                ...

            render_settings()
        elif state == State.GAME:
            if state != last_state:
                camera = base_camera()
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

                reload_game()

            last_state = state
            render_game()
        elif state == State.RENDER_SOLVING:
            if state != last_state:
                camera = base_camera()
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

                reset_animation()

            last_state = state
            render_solving()
        elif state == State.SOLVING_LOADING:
            if state != last_state:
                indice = 0
                nombre_deplacements = 0
                grille_initiale = grille_actuelle[:]

                loading_thread = threading.Thread(target=load_solution)
                loading_thread.start()

            last_state = state
            render_loading_screen()

            if not loading_thread.is_alive():
                state = State.RENDER_SOLVING
        elif state == State.SOLVING_SETTINGS:
            if state != last_state:
                grille_actuelle = grille_initiale[:]
                if last_state != State.RENDER_SOLVING:
                    grille_actuelle = tq.generer_grille_aleatoire(True)

            last_state = state
            render_resolve_settings()

    pr.close_window()


if __name__ == '__main__':
    init()
    # render_solving(plateau, deplacements)
    run()
