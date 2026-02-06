from setuptools import find_packages, setup

package_name = 'my_math_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
          'path_generator = my_math_pkg.path_generator:main',
          'new_path_generator = my_math_pkg.new_path_generator:main',
          'simple_follower = my_math_pkg.simple_follower:main',
        ],
    },
)
