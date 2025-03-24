python ./generate_resources_file.py \
    ./../src/quack2tex/resources \
    ./../src/quack2tex/resources/resources.qrc

pyside6-rcc ./../src/quack2tex/resources/resources.qrc \
 | sed '0,/PySide6/s//PyQt6/' > ./../src/quack2tex/resources/resources_rc.py

