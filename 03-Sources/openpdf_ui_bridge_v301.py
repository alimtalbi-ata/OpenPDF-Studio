"""V30.1: connect legacy GUI operations to conversion controller. Abdelhalim Talbi."""
from types import MethodType
from openpdf_ui_bridge_v300 import connect as connect_pdf
from openpdf_conversion_controller_v301 import ConversionController
from openpdf_core_v260 import pdf_to_docx, pdf_to_xlsx, pdf_to_pptx, extract_text

CONVERSION_ROUTES = {pdf_to_docx:'docx', pdf_to_xlsx:'xlsx', pdf_to_pptx:'pptx', extract_text:'txt'}

def connect(app):
    connect_pdf(app)
    if getattr(app, '_v301_connected', False):
        return app
    original = app._run_pdf
    def routed(self, operation, *args):
        kind = CONVERSION_ROUTES.get(operation)
        if kind is not None:
            if len(args) != 2:
                raise ValueError('La conversion nécessite source et destination')
            def worker(*, progress=None, cancelled=None):
                if cancelled is not None and cancelled():
                    raise RuntimeError('Conversion annulée avant exécution')
                result = ConversionController().convert(args[0], args[1], kind)
                if progress is not None:
                    progress(1, 1)
                return str(result.destination)
            return original(worker)
        return original(operation, *args)
    app._run_pdf = MethodType(routed, app)
    app._v301_connected = True
    # Add a discoverable conversion menu to the actual Tk application.
    # The legacy PDF toolbar remains untouched.
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from pathlib import Path
    if isinstance(app, tk.Tk):
        menubar = app.cget('menu')
        menu = app.nametowidget(menubar) if menubar else tk.Menu(app)
        conversions = tk.Menu(menu, tearoff=False)
        def choose(operation, ext):
            source = filedialog.askopenfilename(parent=app, title='PDF source', filetypes=[('PDF', '*.pdf')])
            if not source:
                return
            destination = filedialog.asksaveasfilename(parent=app, title='Exporter en ' + ext.upper(),
                defaultextension='.'+ext, initialfile=Path(source).stem+'.'+ext,
                filetypes=[(ext.upper(), '*.'+ext)])
            if not destination:
                return
            if Path(destination).exists() and not messagebox.askyesno('Remplacement',
                'Remplacer le fichier de destination ?', parent=app):
                return
            app._run_pdf(operation, source, destination)
        for title, operation, ext in (
            ('PDF vers Word (texte éditable)', pdf_to_docx, 'docx'),
            ('PDF vers Excel (lignes de texte)', pdf_to_xlsx, 'xlsx'),
            ('PDF vers PowerPoint (texte)', pdf_to_pptx, 'pptx'),
            ('Extraire le texte (.txt)', extract_text, 'txt'),
        ):
            conversions.add_command(label=title, command=lambda op=operation, e=ext: choose(op, e))
        menu.add_cascade(label='Conversions', menu=conversions)
        app.configure(menu=menu)
    return app
