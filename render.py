import collections
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
    APPLY_SETTINGS = 7


# constantes
POSITIONS: list[PositionCase]

BASE_CAMERA_POS = [0., 16.0, 5.0]
BUTTON_BG = pr.Color(50, 75, 255, 255)
BUTTON_BG_HOVERED = pr.Color(50, 125, 255, 255)
NUM_TEXTURE_SIZE = 200

# variables globales
camera: pr.Camera3D
font: pr.Font
num_textures: list[pr.Texture] = []
num_textures_for_2d: list[pr.Texture] = []
blocks_models: list[pr.Model] = []
state = State.TITLE_SCREEN
last_state = State.TITLE_SCREEN

positions: list[PositionCase]

grille_initiale: list[int] = []
grille_actuelle: list[int] = []
nombre_deplacements = 0
solution: tq.Etat | None
deplacements: collections.deque[tq.Card] = collections.deque()
liste_deplacements_initiale: list[tq.Card] = []

settings_duree_animation = 0.5
settings_taille_grille = tq.DIM_GRILLE
settings_color_set = 1

total_t = 0
animating = False
bloc_depart = PositionCase(0., 0.)
bloc_arrivee = PositionCase(0., 0.)

resolve_texture: pr.Texture
play_texture: pr.Texture
settings_texture: pr.Texture
reload_texture: pr.Texture


def generate_base_positions():
    global POSITIONS, positions
    POSITIONS = []
    half = tq.DIM_GRILLE // 2
    for i in range(0, tq.DIM_GRILLE):
        for j in range(0, tq.DIM_GRILLE):
            POSITIONS.append(PositionCase(j - half, i - half))
    positions = POSITIONS[:]


def generate_cubes():
    global font, num_textures, num_textures_for_2d, blocks_models, camera

    for i in num_textures:
        pr.unload_texture(i)
    for i in num_textures_for_2d:
        pr.unload_texture(i)
    for i in blocks_models:
        pr.unload_model(i)
    num_textures.clear()
    num_textures_for_2d.clear()
    blocks_models.clear()

    render_tex = pr.load_render_texture(NUM_TEXTURE_SIZE, NUM_TEXTURE_SIZE)

    font_size = NUM_TEXTURE_SIZE
    max_value_str = str(tq.NOMBRE_TUILES - 1)
    if len(max_value_str) >= 3:
        font_size /= len(max_value_str) - 1

    for i in range(0, tq.NOMBRE_TUILES):
        pr.begin_texture_mode(render_tex)

        bg_color: pr.Color
        if settings_color_set == 1:
            bg_color = pr.Color(int(0 + (i / tq.NOMBRE_TUILES) * 155), 0, int(255 - (i / tq.NOMBRE_TUILES) * 155), 255)
        elif settings_color_set == 2:
            bg_color = pr.Color(int(0 + (i / tq.NOMBRE_TUILES) * 155), 0, 0, 255)
        else:
            bg_color = pr.Color(int(0 + (i / tq.NOMBRE_TUILES) * 155), int(0 + (i / tq.NOMBRE_TUILES) * 155),
                                int(0 + (i / tq.NOMBRE_TUILES) * 155), 255)

        pr.clear_background(bg_color)

        text = str(i)
        text_size = pr.measure_text_ex(font, text, font_size, 1.)
        pr.draw_text_ex(font, text, pr.Vector2(int((render_tex.texture.width - text_size.x) / 2),
                                               int((render_tex.texture.height - text_size.y) / 2)),
                        font_size, 1., pr.WHITE)
        pr.end_texture_mode()

        img = pr.load_image_from_texture(render_tex.texture)
        num_textures.append(pr.load_texture_from_image(img))
        img = pr.load_image_from_texture(render_tex.texture)
        pr.image_flip_vertical(img)
        num_textures_for_2d.append(pr.load_texture_from_image(img))

    for i in range(0, tq.NOMBRE_TUILES):
        mesh = pr.gen_mesh_cube(2., 2., 2.)
        model = pr.load_model_from_mesh(mesh)

        model.materials[0].maps[pr.MaterialMapIndex.MATERIAL_MAP_ALBEDO].texture = num_textures[i]

        blocks_models.append(model)

    return


def init():
    global camera, font, num_textures, blocks_models, grille_actuelle, deplacements
    pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT | pr.ConfigFlags.FLAG_VSYNC_HINT)

    pr.init_window(800, 450, "Taquin")
    pr.set_window_state(pr.ConfigFlags.FLAG_WINDOW_RESIZABLE)
    pr.set_window_min_size(800, 450)
    pr.set_target_fps(pr.get_monitor_refresh_rate(pr.get_current_monitor()))

    camera = pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                         [0.0, 1.0, 0.0], 45.0, 0)
    pr.set_camera_mode(camera, pr.CameraMode.CAMERA_FREE)

    global settings_texture, play_texture, resolve_texture, reload_texture
    resolve_texture = pr.load_texture('resources/image/idea.png')
    play_texture = pr.load_texture('resources/image/play.png')
    settings_texture = pr.load_texture('resources/image/setting.png')
    reload_texture = pr.load_texture('resources/image/reload.png')
    font = pr.load_font_ex("resources/font/JetBrainsMono.ttf", 200, None, 0)

    generate_cubes()

    generate_base_positions()
    deplacements = collections.deque([tq.Card.NORD])

    for i in range(0, tq.NOMBRE_TUILES):
        grille_actuelle.append(i)
    grille_actuelle.append(-1)


def get_case(grille: list[int], ligne: int, colonne: int):
    return grille[ligne * tq.DIM_GRILLE + colonne]


def set_case(grille: list[int], ligne: int, colonne: int, valeur: int):
    grille[ligne * tq.DIM_GRILLE + colonne] = valeur


def swap_cases(grille: list[int], ligne_1: int, colonne_1: int, ligne_2: int, colonne_2: int):
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
    if total_t >= settings_duree_animation:
        positions[arrivee.ligne * tq.DIM_GRILLE +
                  arrivee.colonne] = POSITIONS[arrivee.ligne * tq.DIM_GRILLE + arrivee.colonne]
        animating = False
        total_t = 0.0
        return
    normal_time = total_t / settings_duree_animation
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
            nouvelle_pos_vide = PositionCase(
                case_vide.ligne + 1, case_vide.colonne)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_DOWN):
        if case_vide.ligne != 0:
            nouvelle_pos_vide = PositionCase(
                case_vide.ligne - 1, case_vide.colonne)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_LEFT):
        if case_vide.colonne != tq.DIM_GRILLE - 1:
            nouvelle_pos_vide = PositionCase(
                case_vide.ligne, case_vide.colonne + 1)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_RIGHT):
        if case_vide.colonne != 0:
            nouvelle_pos_vide = PositionCase(
                case_vide.ligne, case_vide.colonne - 1)

    if case_vide != nouvelle_pos_vide:
        swap_cases(grille_actuelle, case_vide.ligne, case_vide.colonne,
                   nouvelle_pos_vide.ligne, nouvelle_pos_vide.colonne)
        animating = True
        bloc_depart = nouvelle_pos_vide
        bloc_arrivee = case_vide
        nombre_deplacements += 1


def process_move():
    global animating, bloc_depart, bloc_arrivee, deplacements, nombre_deplacements

    if animating:
        return

    case_vide = get_position_valeur(grille_actuelle, -1)
    nouvelle_pos_vide = case_vide

    deplacement = deplacements.popleft()

    if deplacement == tq.Card.NORD:
        nouvelle_pos_vide = PositionCase(
            case_vide.ligne - 1, case_vide.colonne)
    elif deplacement == tq.Card.SUD:
        nouvelle_pos_vide = PositionCase(
            case_vide.ligne + 1, case_vide.colonne)
    elif deplacement == tq.Card.OUEST:
        nouvelle_pos_vide = PositionCase(
            case_vide.ligne, case_vide.colonne - 1)
    elif deplacement == tq.Card.EST:
        nouvelle_pos_vide = PositionCase(
            case_vide.ligne, case_vide.colonne + 1)

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
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_POINTING_HAND)
        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            global state
            state = target_state
    pr.draw_rectangle(8, pr.get_render_height() -
                      40, text_width + 4, 30, bg_color)
    pr.draw_text("Retour", 10, pr.get_render_height() - 40, 30, pr.BLACK)


def reset_game():
    global nombre_deplacements, grille_actuelle, grille_initiale
    nombre_deplacements = 0
    grille_actuelle = grille_initiale[:]


def draw_reload_button(position: pr.Vector2, size: int):
    button_scale = size / reload_texture.width
    bg_color = BUTTON_BG

    if pr.check_collision_point_circle(pr.get_mouse_position(), pr.Vector2(int(position.x + size / 2),
                                                                           int(position.y + size / 2)), size / 2):
        bg_color = BUTTON_BG_HOVERED
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_POINTING_HAND)

        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            if state == State.GAME:
                reset_game()
            elif state == State.RENDER_SOLVING:
                restart_solving()
        elif pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_RIGHT):
            if state == State.GAME:
                reload_game()

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
        x: float
        if tq.DIM_GRILLE % 2 == 0:
            x = 1.0
        else:
            x = 0
        if val != -1:
            pr.draw_model(blocks_models[val], pr.Vector3(positions[i].ligne * 2. + x, 1., positions[i].colonne * 2 + x),
                          0.9, pr.WHITE)
    pr.end_mode_3d()


def render_solved_text():
    global grille_actuelle, animating
    if is_solved() and not animating:
        pr.draw_text("Résolu", 10, 10, 30, pr.GREEN)
    else:
        pr.draw_text("Non résolu", 10, 10, 30, pr.RED)


def restart_solving():
    global nombre_deplacements, grille_actuelle, deplacements
    nombre_deplacements = 0
    grille_actuelle = grille_initiale[:]
    deplacements = collections.deque(liste_deplacements_initiale[:])
    reset_animation()


def render_solving():
    global animating, camera, nombre_deplacements, deplacements

    pr.update_camera(camera)

    if len(deplacements) > 0:
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
    global nombre_deplacements, grille_actuelle, grille_initiale
    nombre_deplacements = 0
    grille_initiale = tq.generer_grille_aleatoire(True)
    grille_actuelle = grille_initiale[:]
    reset_animation()


def render_game():
    global camera, grille_actuelle, animating
    pr.update_camera(camera)

    pr.begin_drawing()

    render_grid()

    render_solved_text()

    draw_nombre_mouvements()

    draw_back_button(State.TITLE_SCREEN)
    pr.draw_text(str(pr.get_fps()), 10, 50, 30, pr.BLACK)

    button_size = 80
    draw_reload_button(pr.Vector2(pr.get_screen_width() - button_size - 10,
                                  pr.get_screen_height() - button_size - 10), button_size)

    pr.end_drawing()

    if not is_solved():
        handle_input()


def get_card_from_number(value):
    if value == 0:
        return tq.Card.NORD
    elif value == 1:
        return tq.Card.OUEST
    elif value == 2:
        return tq.Card.SUD
    else:
        return tq.Card.EST


def draw_state_switch_button(texture: pr.Texture, position: pr.Vector2, size: int, target_state: State):
    button_scale = size / texture.width
    bg_color = BUTTON_BG

    if pr.check_collision_point_circle(pr.get_mouse_position(),
                                       pr.Vector2(int(position.x + size / 2), int(position.y + size / 2)),
                                       size / 2):
        bg_color = BUTTON_BG_HOVERED
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_POINTING_HAND)

        if pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            global state
            state = target_state

    pr.draw_circle(int(position.x + size / 2),
                   int(position.y + size / 2), size / 2, bg_color)
    pr.draw_texture_ex(texture, position, 0., button_scale, pr.WHITE)


def process_title_screen_moves():
    global deplacements, nombre_deplacements
    deplacements.appendleft(get_card_from_number(random.randint(0, 3)))
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
    pr.draw_text("Taquin 3D 2023", int((pr.get_screen_width() -
                                        title_width) / 2), 50, 70, pr.Color(150, 50, 50, 255))

    pr.end_drawing()


def render_loading_screen():
    pr.update_camera(camera)
    pr.begin_drawing()
    pr.clear_background(pr.GRAY)
    pr.begin_mode_3d(camera)
    pr.end_mode_3d()
    reload_icon_size = 50
    pr.draw_text(str(tq.nombre_etats_explo), 0, 0, 30, pr.BLACK)

    pr.draw_texture_pro(reload_texture,
                        pr.Rectangle(0, 0, reload_texture.width,
                                     reload_texture.height),
                        pr.Rectangle(int(pr.get_screen_width() / 2),
                                     int(pr.get_screen_height() / 2),
                                     reload_icon_size, reload_icon_size),
                        pr.Vector2(reload_icon_size / 2, reload_icon_size / 2),
                        - (pr.get_time() % 30. * 360.), pr.WHITE)

    draw_back_button(State.SOLVING_SETTINGS)

    pr.end_drawing()


SETTINGS_PANEL_MARGIN = 10


def draw_scroll_setting(height: int, setting_name: str, unit_name: str, current_value: float, min_value: float,
                        max_value: float, step: float):
    font_size = 30
    contenu = setting_name + " "
    size = int(pr.measure_text(contenu, font_size))
    value = round(current_value, 1)
    position = pr.Vector2(pr.get_screen_width() / 2 - size,
                          SETTINGS_PANEL_MARGIN + 10 + height * (font_size + SETTINGS_PANEL_MARGIN))
    color = pr.BLACK

    if pr.check_collision_point_rec(pr.get_mouse_position(),
                                    pr.Rectangle(position.x, position.y,
                                                 size + pr.measure_text(str(value) + unit_name, font_size), font_size)):
        color = pr.GRAY
        if pr.get_mouse_wheel_move_v().y > 0 or pr.is_key_pressed(pr.KeyboardKey.KEY_UP):
            current_value = min(max_value, current_value + step)
        elif pr.get_mouse_wheel_move_v().y < 0 or pr.is_key_pressed(pr.KeyboardKey.KEY_DOWN):
            current_value = max(min_value, current_value - step)

    pr.draw_text(contenu + str(value) + unit_name,
                 int(position.x), int(position.y), font_size, color)

    return current_value


def render_settings():
    global settings_duree_animation, settings_taille_grille, settings_color_set
    process_title_screen_moves()

    pr.begin_drawing()
    render_grid()

    pr.draw_rectangle(SETTINGS_PANEL_MARGIN, SETTINGS_PANEL_MARGIN,
                      pr.get_screen_width() - SETTINGS_PANEL_MARGIN * 2,
                      pr.get_render_height() - SETTINGS_PANEL_MARGIN * 2, pr.Color(255, 255, 255, 220))

    settings_duree_animation = draw_scroll_setting(0, "Durée d'animation", "s", settings_duree_animation, 0.2, 1.5, 0.1)

    settings_taille_grille = int(draw_scroll_setting(1, "Taille grille", "", settings_taille_grille, 3, 5, 1))

    old_settings_color_set = settings_color_set
    settings_color_set = int(draw_scroll_setting(2, "Couleurs blocs", "", settings_color_set, 1, 3, 1))

    draw_back_button(State.TITLE_SCREEN)
    pr.end_drawing()

    if settings_taille_grille != tq.DIM_GRILLE:
        set_dim_grille(settings_taille_grille)

    if old_settings_color_set != settings_color_set:
        generate_cubes()


case_selectionee = 0

selected_cases = [-1, -1]


def render_solving_settings():
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

    if soluble:
        text = "Difficulté : " + str(tq.heuristique(tq.K, grille_actuelle))
        pr.draw_text(text, 10, 40, 30, pr.BLACK)

    taille_case = (min(pr.get_screen_width(), pr.get_screen_height()) * 0.75) / tq.DIM_GRILLE
    case_scale = taille_case / num_textures_for_2d[0].width

    hovered_case = -1

    global selected_cases
    for i in range(0, tq.NOMBRE_CASES):
        x: float
        if tq.DIM_GRILLE % 2 == 0:
            x = tq.DIM_GRILLE // 2
        else:
            x = tq.DIM_GRILLE // 2 + 0.5
        position = pr.Vector2(
            int(pr.get_screen_width() / 2 +
                taille_case * (i % tq.DIM_GRILLE - x)),
            int(pr.get_screen_height() / 2 +
                taille_case * (i // tq.DIM_GRILLE - x)))
        if grille_actuelle[i] != -1:
            pr.draw_texture_ex(num_textures_for_2d[grille_actuelle[i]],
                               position,
                               0,
                               case_scale,
                               pr.WHITE)

            pr.draw_rectangle_lines_ex(pr.Rectangle(int(position.x), int(position.y), taille_case, taille_case),
                                       2., pr.WHITE)

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
    if tq.DIM_GRILLE == 3:
        text = "Set de poids " + str(tq.K)
        font_size = 30
        text_width = pr.measure_text(text, font_size)

        pr.draw_text(text, int((pr.get_screen_width() - text_width) / 2),
                     pr.get_screen_height() - font_size - 10, font_size, pr.BLACK)

        if pr.get_mouse_wheel_move_v().y > 0:
            tq.set_weight_set(tq.K + 1)
        elif pr.get_mouse_wheel_move_v().y < 0:
            tq.set_weight_set(tq.K - 1)

    if hovered_case != -1:
        tooltip = "poids = " + str(tq.get_poids_tuile(tq.K, hovered_case))
        pr.draw_rectangle(int(pr.get_mouse_position().x + 18), int(pr.get_mouse_position().y),
                          pr.measure_text(tooltip, 20) + 4, 20, pr.BLACK)
        pr.draw_text(tooltip, int(pr.get_mouse_position().x + 20),
                     int(pr.get_mouse_position().y), 20,
                     pr.WHITE)

    draw_back_button(State.TITLE_SCREEN)
    pr.end_drawing()


def load_solution():
    global deplacements, solution, liste_deplacements_initiale
    solution = tq.astar(grille_actuelle)
    if solution is not None:
        liste_deplacements_initiale = solution.liste_deplacement[:]
        deplacements = collections.deque(liste_deplacements_initiale)


def base_camera():
    return pr.Camera3D(BASE_CAMERA_POS[:], [0.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0], 45.0, 0)


def run():
    global animating, camera, state, last_state, grille_actuelle, grille_initiale, positions
    global nombre_deplacements, deplacements

    random.seed()

    last_state = State.INIT
    state = State.TITLE_SCREEN

    loading_thread: threading.Thread = threading.Thread()

    while not pr.window_should_close():
        if pr.is_key_pressed(pr.KeyboardKey.KEY_R):
            camera = base_camera()
        pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_DEFAULT)
        if state == State.TITLE_SCREEN:
            if state != last_state:
                camera = base_camera()
                camera.position.z = 18.
                pr.set_camera_mode(camera, pr.CameraMode.CAMERA_ORBITAL)
                grille_actuelle = tq.generer_grille_aleatoire()
                deplacements = collections.deque()
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
                nombre_deplacements = 0
                grille_initiale = grille_actuelle[:]

                loading_thread = threading.Thread(target=load_solution)
                loading_thread.start()

            last_state = state
            render_loading_screen()

            if not loading_thread.is_alive():
                state = State.RENDER_SOLVING
            elif state == State.SOLVING_SETTINGS:
                tq.quit_solving()
                loading_thread.join()
        elif state == State.SOLVING_SETTINGS:
            if state != last_state:
                tq.reset_solving()
                grille_actuelle = grille_initiale[:]
                if last_state != State.RENDER_SOLVING:
                    grille_actuelle = tq.generer_grille_aleatoire(True)

            last_state = state
            render_solving_settings()

    pr.close_window()
    tq.quit_solving()


def set_dim_grille(new_dim: int):
    global settings_taille_grille, grille_actuelle
    if new_dim <= 1:
        return
    reset_animation()
    tq.set_dim_grille(new_dim)
    settings_taille_grille = tq.DIM_GRILLE
    grille_actuelle = tq.generer_grille_aleatoire(True)
    generate_base_positions()
    generate_cubes()


if __name__ == '__main__':
    # NE RIEN METTRE AVANT INIT
    init()
    run()
