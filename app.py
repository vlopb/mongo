from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from bson import ObjectId
from mongo import client

app = Flask(__name__)

db = client['nombre_de_tu_base_de_datos']
eventos_collection = db['eventos']

class Evento:
    def __init__(self, titulo, fecha, categoria, realizado=False):
        self.titulo = titulo
        self.fecha = fecha if isinstance(fecha, datetime) else datetime.combine(fecha, datetime.min.time())
        self.categoria = categoria
        self.realizado = realizado

    def to_dict(self):
        return {
            'titulo': self.titulo,
            'fecha': self.fecha,
            'categoria': self.categoria,
            'realizado': self.realizado
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            titulo=data['titulo'],
            fecha=data['fecha'],
            categoria=data['categoria'],
            realizado=data.get('realizado', False)
        )

class Agenda:
    @staticmethod
    def agregar_evento(titulo, fecha_str, categoria):
        fecha = Agenda.validar_fecha(fecha_str)
        if fecha:
            nuevo_evento = Evento(titulo, fecha, categoria, realizado=False)
            eventos_collection.insert_one(nuevo_evento.to_dict())
            return True
        return False

    @staticmethod
    def validar_fecha(fecha_str):
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            return None

    @staticmethod
    def obtener_eventos_por_realizar():
        eventos = eventos_collection.find({'realizado': False})
        return [Evento.from_dict(e) for e in eventos]

    @staticmethod
    def obtener_eventos_realizados():
        eventos = eventos_collection.find({'realizado': True})
        return [Evento.from_dict(e) for e in eventos]

    @staticmethod
    def alternar_estado_evento(evento_id):
        evento = eventos_collection.find_one({'_id': ObjectId(evento_id)})
        if evento:
            nuevo_estado = not evento.get('realizado', False)
            eventos_collection.update_one(
                {'_id': ObjectId(evento_id)},
                {'$set': {'realizado': nuevo_estado}}
            )

    @staticmethod
    def eliminar_evento(evento_id):
        eventos_collection.delete_one({'_id': ObjectId(evento_id)})

agenda = Agenda()

@app.route('/')
def index():
    eventos_por_realizar = agenda.obtener_eventos_por_realizar()
    return render_template('index.html', eventos=eventos_por_realizar)

@app.route('/realizados')
def eventos_realizados():
    eventos_realizados = agenda.obtener_eventos_realizados()
    return render_template('realizados.html', eventos=eventos_realizados)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_evento():
    if request.method == 'POST':
        titulo = request.form['titulo']
        fecha = request.form['fecha']
        categoria = request.form['categoria']
        if agenda.agregar_evento(titulo, fecha, categoria):
            return redirect(url_for('index'))
        else:
            return "Error: La fecha no es válida"
    return render_template('agregar.html')

@app.route('/alternar_estado/<evento_id>', methods=['POST'])
def alternar_estado(evento_id):
    agenda.alternar_estado_evento(evento_id)
    return redirect(request.referrer or url_for('index'))

@app.route('/eliminar/<evento_id>', methods=['POST'])
def eliminar_evento(evento_id):
    agenda.eliminar_evento(evento_id)
    return redirect(request.referrer or url_for('index'))

@app.route('/calendario')
def calendario():
    return render_template('calendario.html')

@app.route('/api/eventos')
def api_eventos():
    # Obtener todos los eventos y formatearlos para el calendario
    eventos = eventos_collection.find()
    eventos_json = []
    for evento in eventos:
        eventos_json.append({
            'title': evento['titulo'],
            'start': evento['fecha'].strftime('%Y-%m-%d'),
            'description': f"Categoría: {evento['categoria']}, Estado: {'Realizado' if evento['realizado'] else 'Por realizar'}"
        })
    return {'events': eventos_json}

if __name__ == '__main__':
    app.run(debug=True)
