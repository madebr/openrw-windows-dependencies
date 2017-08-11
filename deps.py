import shutil

DEPENDENCIES = (
    'bullet3',
    'glm',
    'ffmpeg',
    'openal-soft',
    'sdl2'
)


def fix_bullet3(path):
    lib_deb_path = path / 'debug' / 'lib'
    lib_names = (
        'BulletCollision',
        'BulletDynamics',
        'BulletSoftBody',
        'LinearMath'
    )
    for lib_name in lib_names:
        orig_lib = lib_deb_path / (lib_name + '_Debug.lib')
        targ_lib = lib_deb_path / (lib_name + '.lib')
        try:
            shutil.move(src=str(orig_lib), dst=str(targ_lib))
        except FileNotFoundError:
            pass  # Assume fix is already applied


def fix_SDL2(path):
    lib_deb_path = path / 'debug' / 'lib'
    lib_names = (
        'SDL2',
        'SDL2main',
    )
    for lib_name in lib_names:
        orig_lib = lib_deb_path / (lib_name + 'd.lib')
        targ_lib = lib_deb_path / (lib_name + '.lib')
        try:
            shutil.move(src=str(orig_lib), dst=str(targ_lib))
        except FileNotFoundError:
            pass  # Assume fix is already applied


COPY_FIXES = {
    'bullet3': fix_bullet3,
    'sdl2': fix_SDL2,
}
