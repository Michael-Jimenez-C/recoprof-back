from db.engine import Engine
from fastapi import APIRouter, HTTPException, Depends
from odmantic import ObjectId
from db.models import Profesor, Comentario, Notas, Asignatura
import responseBody as rb
from typing import Annotated
from .auth import access
from validations.Values import FacultadesValidas
router = APIRouter(
    tags=["profesor"],
    prefix="/api/profesor"
)

@router.get('/list', response_model = rb.PaginacionProfesor)
async def list_profesores(page: int = 0, limit: int = 10, name:str = ''):
    name = name.upper()

    args = [Profesor, Profesor.nombre.match("[A-z0-9 ]*"+name+"[A-z0-9 ]*")]
    kwargs = {"skip":page*limit, "limit":limit}
    total = await Engine.count(*args)
    profesores = await Engine.find(*args, **kwargs)
    profesores_simplificadas = [
        rb.ProfesorConAsignatura(**profesor.model_dump(),
            asignaturas_nombre = [
                rb.AsignaturasBase(**(asign.model_dump()))
                 for asign in (await Engine.find(Asignatura,Asignatura.id.in_(profesor.asignaturas)))])
        for profesor in profesores
    ]

    return {"contenido":profesores_simplificadas,
            "total": total,
            "total_paginas": (total + limit - 1) // limit if limit > 0 else 1}

@router.get('/{profesor_id}', response_model=Profesor)
async def get_profesor(profesor_id: ObjectId):
    try:
        response = await Engine.find_one(Profesor, Profesor.id==profesor_id)

    except:
        HTTPException(status_code=404, detail="not found")
    return response

@router.get('/puntaje/{profesor_id}', response_model=Profesor)
async def get_profesor(profesor_id: ObjectId):
    try:
        response = await Engine.find(Notas, Notas.profesor==profesor_id)
    except:
        HTTPException(status_code=404, detail="not found")
    return response

@router.post('/create', response_model=Profesor)
async def create_profesor(profesor: Profesor, acc: Annotated[bool, Depends(access)]):
    profesor.nombre = profesor.nombre.upper()
    return await Engine.save(profesor)

@router.delete('/delete/{profesor_id}')
async def delete_profesor(profesor_id: ObjectId, acc: Annotated[bool, Depends(access)]):
    if not acc:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        await Engine.remove(Profesor, Profesor.id==profesor_id)
        await Engine.remove(Comentario, Comentario.profesor==profesor_id)
        await Engine.remove(Notas, Notas.profesor==profesor_id)
    except:
        HTTPException(status_code=404, detail="not found")
    return {"status": "ok"}

@router.get('/facultad/{facultad}', response_model = rb.PaginacionProfesorPorFacultad)
async def get_asignatura_facultad(facultad: FacultadesValidas, page: int = 0, limit: int = 10, name:str = ""):
    name = name.upper()
    total = await Engine.count(Profesor, Profesor.nombre.match("[A-z ]*"+name+"[A-z ]*"), Profesor.facultades == facultad)
    
    profesores = await Engine.find(
        Profesor,
        Profesor.nombre.match("[A-z0-9 ]*"+name+"[A-z0-9 ]*"),
        Profesor.facultades == facultad,
        skip=page*limit,
        limit=limit
    )
    
    total_paginas = (total + limit - 1) // limit if limit > 0 else 1
    
    profesores_simplificadas = [
        rb.ProfesorPorFacultad(**profesor.model_dump(),
            asignaturas_nombre = [
                rb.Asignatura(**(asign.model_dump()))
                 for asign in (await Engine.find(Asignatura,Asignatura.id.in_(profesor.asignaturas)))])
        for profesor in profesores
    ]

    return {
        "contenido": profesores_simplificadas,
        "total": total,
        "total_paginas": total_paginas
    }