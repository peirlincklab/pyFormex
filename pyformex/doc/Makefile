RST2MAN:= /usr/share/docutils/scripts/python3/rst2man

manpages: pyformex.1

pyformex.1: pyformex.1.rst
	$(RST2MAN) $< > $@

clean:
	rm -f pyformex.1
