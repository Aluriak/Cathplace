

gui: qtgui
qtgui:
	python -m qtgui
tkgui:
	python -m tkgui

solve:
	clingo 0 humans.lp offices.lp engine.lp -W no-atom-undefined
dbg:
	clingo 0 humans.lp offices.lp engine.lp
txt:
	clingo 0 humans.lp offices.lp engine.lp --text
