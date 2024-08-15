python ./generate_resources_file.py \
    ./../src/quack2tex/resources \
    ./../src/quack2tex/resources/resources.qrc

pyside6-rcc -o ./../src/quack2tex/resources/resources_rc.py \
    ./../src/quack2tex/resources/resources.qrc
