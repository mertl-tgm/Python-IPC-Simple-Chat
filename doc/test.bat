@echo "Making LaTeX"
make latex
( cd _build/latex/; make ) # the LaTeX needs to be built separately. This can be done in a subshell
@echo "Done making LaTeX"
@echo "Copying PDF to Static"
cp _build/latex/Genetic.pdf _build/html/_static/
@echo "Copy PDF to Static... DONE"
@echo "Adding PDF to HTML"
sed -i '' 's/lorem\ ipsum/\<a href="_static\/Genetic.pdf"\>Download\ Me\<\/a\>/g' _build/html/downloadPDF.html
@echo "Done adding PDF to HTML"
@echo "Removing LaTeX dir"
rm -rf _build/latex
@echo "Done removing LaTeX dir"

$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
@echo
@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."