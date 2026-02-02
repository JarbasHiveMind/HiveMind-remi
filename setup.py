from setuptools import setup

setup(
    name='hivemind-remi',
    version='0.0.1',
    packages=['hivemind_remi'],
    include_package_data=True,
    install_requires=["remi", "hivemind_bus_client~=0.4.4"],
    url='https://github.com/JarbasHiveMind/HiveMind-remi',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    entry_points={
        'console_scripts': [
            'HiveMind-remi=hivemind_remi.__main__:main'
        ]
    }
)
