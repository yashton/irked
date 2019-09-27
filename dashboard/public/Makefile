.PHONY: all setup flot jquery-ui d3

THEME=trontastic

all: setup

setup: flot jquery-ui d3 irked.log

irked.log: ../../irked.log
	tail ../../irked.log > irked.log
#	ln -s ../irked.log

flot: js/flot-0.7.tar.gz
	cd js; \
	tar xzf flot-0.7.tar.gz; \
	ln -s flot/excanvas.js; \
	ln -s flot/excanvas.min.js; \
	ln -s flot/jquery.flot.js; \
	ln -s flot/jquery.flot.min.js

jquery-ui: js/jquery-ui-1.8.19.custom.zip
	cd js; \
	unzip -q jquery-ui-1.8.19.custom.zip -d jquery-ui; \
	ln -s jquery-ui/js/jquery-ui-1.8.19.custom.min.js jquery-ui.min.js; \
	ln -s jquery-ui/development-bundle/ui/jquery-ui-1.8.19.custom.js jquery-ui.js;
	find js/jquery-ui -type d | xargs chmod a+rx
	cd css; \
	ln -s ../js/jquery-ui/css/$(THEME)/jquery-ui-1.8.19.custom.css jquery-ui.css; \
	ln -s ../js/jquery-ui/css/$(THEME)/images;

theme:
	rm -f css/images css/jquery-ui.css
	cd css; \
	ln -s ../js/jquery-ui/css/$(THEME)/jquery-ui-1.8.19.custom.css jquery-ui.css; \
	ln -s ../js/jquery-ui/css/$(THEME)/images;

d3: js/mbostock-d3-v2.8.1-0-gaf2af6a.zip
	cd js; \
	unzip -q mbostock-d3-v2.8.1-0-gaf2af6a.zip; \
	mv mbostock-d3-224acae d3; \
	ln -s d3/d3.v2.js; \
	ln -s d3/d3.v2.min.js;

clean:
	rm -f irked.log
	rm -rf js/flot
	rm -f js/excanvas.js js/excanvas.min.js js/jquery.flot.js js/jquery.flot.min.js
	rm -rf js/jquery-ui
	rm -f js/jquery-ui.js js/jquery-ui.min.js
	rm -f css/jquery-ui.css;
	rm -rf css/images
	rm -rf js/d3
	rm -f js/d3.v2.js js/d3.v2.min.js