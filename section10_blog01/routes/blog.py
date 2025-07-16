from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from db.database import direct_get_conn, context_get_conn
from sqlalchemy import text, Connection
from sqlalchemy.exc import SQLAlchemyError
from schemas.blog_schema import BlogData
from utils import util

# router 생성
router = APIRouter(prefix="/blogs", tags=["blogs"])
#jinja2 Template 엔진 생성
templates = Jinja2Templates(directory="templates")
"/blogs"

@router.get("/")
async def get_all_blogs(request: Request):
    conn = None
    try:
        conn = direct_get_conn()
        query ="""
        SELECT id, title, author, content, image_loc, modified_dt FROM blog
        """
        result = conn.execute(text(query))
        all_blogs = [BlogData(id = row.id,
                     title = row.title,
                     author = row.author,
                     content = util.truncate_text(row.content),
                     image_loc = row.image_loc, #Null -> None으로 바뀌면서 None으로 들어가게 된다.
                     modified_dt=row.modified_dt)
                     for row in result]
        #만약에 row.image_loc1이렇게 쓰면 SQLAlchemyError가 잡지 못한다. 그럴때는 default exception을 써준다.
        result.close()
        return templates.TemplateResponse(
            request =  request,
            name = "index.html",
            context = {"all_blogs": all_blogs}
        )
    except SQLAlchemyError as e:
        #부하나 락이 많이 걸릴 때가 많이 쓰임.(권한 문제)
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알 수 없는 이유로 서비스 오류가 발생하였습니다.")
    finally:
        if conn:
            conn.close()

@router.get("/show/{id}") 
async def get_blog_by_id(request: Request, id:int,
                     conn: Connection = Depends(context_get_conn)): #fastapi가 context_get_conn 함수를 불러서 그 결과를 반환해서 여기에 넣어준다.
    try:
        query = f"""
        SELECT id, title, author, content, image_loc, modified_dt from blog
        where id = :id
        """
        stmt = text(query)
        bind_stmt = stmt.bindparams(id=id)
        result = conn.execute(bind_stmt) 
        #만약에 1건도 찾지 못하면 오류를 던지는 로직
        if result.rowcount == 0 :
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"해당 id {id}는(은) 존재하지 않습니다.")
    

        row = result.fetchone()
        blog = BlogData(id=row[0],
                 title=row[1],
                 author=row[2],
                 content=util.newline_to_br(row[3]),
                 image_loc=row[4],
                 modified_dt=row[5])
        result.close()
        return templates.TemplateResponse(
            request = request,
            name = "show_blog.html",
            context = {"blog":blog}
        )
    
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="알 수 없는 이유로 서비스 오류가 발생하였습니다.")
    #finally:
        #conn.close() -> 하지 않아도 됨.

@router.get("/new")
def create_blog_ui(request: Request):
    return templates.TemplateResponse(
        request = request,
        name = "new_blog.html",
        context = {}
    )
@router.post("/new")
def create_blog(request: Request
                , title = Form(min_length=2, max_length=200)
                , author = Form(max_length=100)
                , content = Form(min_length=2, max_length=4000)
                , conn: Connection = Depends(context_get_conn) #connection값은 마지막에 넣기
                ):
    try:
        query = f"""
        INSERT INTO blog(title, author, content, modified_dt)
        values ('{title}', '{author}', '{content}', now())
        """
        #문자열이므로 '' 표시 반드시 해줘야함.
        conn.execute(text(query))
        conn.commit() #반드시 commit 해줘야함.

        return RedirectResponse("/blogs", status_code=status.HTTP_302_FOUND)
        
    except SQLAlchemyError as e:
        print(e)
        conn.rollback() #안해도됨. close될 때 rollback이 되므로
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="요청데이터가 제대로 전달되지 않았습니다.")
    
@router.get("/modify/{id}")
def update_blog_ui(request: Request,id:int,conn = Depends(context_get_conn)):
    try:
        query = f"""
        SELECT id, title, author, content from blog where id = :id
        """
        stmt = text(query)
        bind_stmt = stmt.bindparams(id=id)
        result = conn.execute(bind_stmt)

        if result.rowcount == 0 :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f"해당 id {id}는(은) 존재하지 않습니다.")
        row = result.fetchone()

        return templates.TemplateResponse(
            request = request,
            name = "modify_blog.html",
            context = {"id": row.id, "title":row.title,
                    "author":row.author, "content":row.content}
        )
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="요청데이터가 제대로 전달되지 않았습니다.")
    
@router.post("/modify/{id}")
def update_blog(request: Request, id: int
                , title = Form(min_length=2, max_length=200)
                , author = Form(max_length=100)
                , content = Form(min_length=2, max_length=4000)
                , conn: Connection = Depends(context_get_conn) #connection값은 마지막에 넣기
                ):
    try:
        query = f"""
        UPDATE blog
        SET title= :title, author= :author, content= :content
        where id = :id
        """
        bind_stmt = text(query).bindparams(id=id, title=title, author=author, content=content)

        result = conn.execute(bind_stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail=f"해당 id {id}는(은) 존재하지 않습니다.")
        conn.commit()
        return RedirectResponse(f"/blogs/show/{id}",status_code=status.HTTP_302_FOUND)
    
    except SQLAlchemyError as e:
        print(e)
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="요청데이터가 제대로 전달되지 않았습니다.")
     
@router.post("/delete/{id}")
def delete_blog(request: Request, id:int,
                conn: Connection = Depends(context_get_conn)):
    try:
        query = f"""
        DELETE FROM blog
        where id = :id
        """
        bind_stmt = text(query).bindparams(id=id)
        result=conn.execute(bind_stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                        detail=f"해당 id {id}는(은) 존재하지 않습니다.")
        conn.commit()
        return RedirectResponse("/blogs",status_code=status.HTTP_302_FOUND)
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="요청하신 서비스가 잠시 내부적으로 문제가 발생하였습니다.")
