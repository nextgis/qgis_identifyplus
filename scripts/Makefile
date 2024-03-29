UI_PATH=../ui
UI_SOURCES=$(wildcard $(UI_PATH)/*.ui)
UI_FILES=$(patsubst $(UI_PATH)/%.ui, $(UI_PATH)/../ui_%.py, $(UI_SOURCES))

LANG_PATH=../i18n
LANG_SOURCES=$(wildcard $(LANG_PATH)/*.ts)
LANG_FILES=$(patsubst $(LANG_PATH)/%.ts, $(LANG_PATH)/%.qm, $(LANG_SOURCES))

RES_PATH=..
RES_SOURCES=$(wildcard $(RES_PATH)/*.qrc)
RES_FILES=$(patsubst $(RES_PATH)/%.qrc, $(RES_PATH)/%_rc.py, $(RES_SOURCES))

PRO_PATH=.
PRO_FILES=$(wildcard $(PRO_PATH)/*.pro)

ALL_FILES= ${RES_FILES} ${UI_FILES} ${LANG_FILES}

all: $(ALL_FILES)

ui: $(UI_FILES)

ts: $(PRO_FILES)
	pylupdate5 -verbose $<

lang: $(LANG_FILES)

res: $(RES_FILES)

$(UI_FILES): $(UI_PATH)/../ui_%.py: $(UI_PATH)/%.ui
	pyuic5 --from-imports -o $@ $<

$(LANG_FILES): $(LANG_PATH)/%.qm: $(LANG_PATH)/%.ts
	lrelease $<

$(RES_FILES): $(RES_PATH)/%_rc.py: $(RES_PATH)/%.qrc
	pyrcc5 -o $@ $<

clean:
	rm -f $(ALL_FILES)
	find -name "*.pyc" -exec rm -f {} \;
	rm -f *.zip

package:
	rm -f identifyplus.zip
	cd ../.. && ln -s qgis_identifyplus identifyplus && rm -f identifyplus.zip && zip -r identifyplus.zip identifyplus -x "*__pycache__*" \*.project \*.pydevproject \*.pyc \.* \doc \*.ts \*.ui \*.qrc \*.pro \*~ \*.git\* \*Makefile* && rm identifyplus
	mv ../../identifyplus.zip .

upload:
	plugin_uploader.py identifyplus.zip
