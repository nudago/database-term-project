from flask import Flask, render_template, redirect, request, flash, url_for, session
import pymysql
from cfg import setting

hotplace_db = pymysql.connect(
    user=setting.DB_CFG['user'],
    passwd=setting.DB_CFG['passwd'],
    host=setting.DB_CFG['host'],
    db=setting.DB_CFG['db'],
    charset=setting.DB_CFG['charset'])
cur = hotplace_db.cursor(pymysql.cursors.DictCursor)

app = Flask(__name__)
app.secret_key = 'ThisIsSomethingSpecial'

@app.route('/')
def main(): #로그인 페이지
    return render_template('login.html')

@app.route('/register')
def register(): #회원가입 페이지
    return render_template('register.html')

@app.route('/register/do', methods=['POST'])
def do_register(): #회원가입 로직
    _id = request.form['id']
    _pw = request.form['pw']
    _username = request.form['username']
    _email = request.form['email']
    cur.execute('SELECT * FROM users WHERE id=(%s)',_id)
    _isAlreadyUse = cur.fetchall()
    
    if (_isAlreadyUse):
        print(1)
        flash('id is alreday in use.')
        return render_template('register.html')
    
    cur.execute('INSERT INTO users (id, password,username, email) VALUES (%s, %s, %s, %s)', (_id, _pw, _username, _email))
    hotplace_db.commit()
    return render_template('register_result.html', id=_id, pw=_pw, username=_username, email=_email)

@app.route('/login', methods=['POST'])
def login(): #로그인
    _id = request.form['id']
    _pw = request.form['pw']
    cur.execute('SELECT * FROM users WHERE id=%s AND password =%s', (_id, _pw))
    account = cur.fetchone()

    if account:
        session['loggedin'] = True
        session['id'] = account['id']
        session['username'] = account['username']
        flash('login Success')
        return redirect(url_for('show_restaurant'))
    else:
        flash('login Failed, Check id and passwrod')
        return render_template('login.html')

@app.route('/logout')
def logout(): #로그아웃
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    print(session)
    return render_template('login.html')

@app.route('/restaurant', methods=['GET'])
def show_restaurant(): # 음식점 검색
    if 'loggedin' in session:
        # _searchCategory = request.form['searchCategory']
        # _toSearch = request.form['toSearch']

        _searchCategory = request.args.get('searchCategory')
        _toSearch = request.args.get('toSearch', "")
        print(_searchCategory) 
        print(_toSearch)
        if _searchCategory == '음식점':
            cur.execute("SELECT * FROM restaurant WHERE restaurant_name LIKE %s ORDER BY avg_rating DESC, restaurant_name", ('%%%s%%' % _toSearch))
        elif _searchCategory == '지역':
            cur.execute("SELECT * FROM restaurant WHERE location LIKE %s ORDER BY avg_rating DESC, restaurant_name", ('%%%s%%' % _toSearch))
        elif _searchCategory == '분류':
            cur.execute("SELECT * FROM restaurant WHERE category LIKE %s ORDER BY avg_rating DESC, restaurant_name", ('%%%s%%' % _toSearch))
        else:
            cur.execute("SELECT * FROM restaurant WHERE location LIKE %s ORDER BY avg_rating DESC, restaurant_name", ('%%%s%%' % _toSearch))
        rows = cur.fetchall()
        return render_template('show_restaurant.html', rows=rows)
    else:
        flash('You need login first.')
        return render_template('login.html')

@app.route('/review/<r_name>')
def show_review(r_name): # 리뷰보기
    if 'loggedin' in session:
        cur.execute("SELECT * FROM review WHERE  r_name=%s", r_name)
        review = cur.fetchall() 
        return render_template('show_review.html', rows=review)

@app.route('/add_bookmark', methods=['GET'])
def add_bookmark(): # 즐겨찾기추가후 리뷰보기
    if 'loggedin' in session:
        add_bookmark = request.args.get('bookmark', "")
        cur.execute("SELECT * FROM review WHERE  r_name=%s", add_bookmark)
        review = cur.fetchall()

        # 북마크 추가
        cur.execute('SELECT * FROM bookmark WHERE u_id=%s AND r_name=%s', (session['id'], add_bookmark))
        isBookmarked = cur.fetchone()
        if isBookmarked:
            flash("Already Bookmarked")
        else:
            cur.execute("INSERT INTO bookmark (u_id, r_name) VALUES (%s, %s)",(session['id'], add_bookmark))
            hotplace_db.commit()
        return render_template('show_review.html', rows=review)
    
@app.route('/add_review/<r_name>')
def add_review(r_name): # 리뷰
    if 'loggedin' in session:
        return render_template('add_review.html', rows=r_name)

@app.route('/save_review', methods=['GET'])
def save_review(): # 리뷰 저장
    _r_name = request.args.get('r_name', "")
    _rating = request.args.get('rating', "")
    _content = request.args.get('review_content', "")

    # 리뷰추가
    cur.execute("INSERT INTO review (u_id, r_name, rating, content) VALUES (%s, %s, %s, %s)", (session['id'], _r_name, _rating, _content))
    hotplace_db.commit()
    return redirect(url_for('show_review', r_name=_r_name))

@app.route('/mypage')
def show_mypage(): # 내 즐겨찾기,리뷰,회원탈퇴 보기
    if 'loggedin' in session: # 레스토랑이름찾고, 다른테이블서 정보GET
        #
        cur.execute("SELECT * FROM restaurant WHERE restaurant_name in (SELECT r_name FROM bookmark WHERE u_id=%s)", session['id'])
        mybookmark = cur.fetchall()
        cur.execute("SELECT * FROM review WHERE u_id=%s", session['id'])
        myreview = cur.fetchall()
        print(mybookmark)
        print(myreview)
        return render_template('show_mypage.html', rows=myreview, books=mybookmark)

@app.route('/delete_review/<r_name>')
def delete_review(r_name): # 리뷰 삭제
    if 'loggedin' in session:
        cur.execute("DELETE FROM review WHERE u_id=%s and r_name=%s", (session['id'], r_name))
        hotplace_db.commit()
        return redirect(url_for('show_mypage'))

@app.route('/delete_bookmark/<r_name>')
def delete_bookmark(r_name): # 북마크 삭제
    if 'loggedin' in session:
        cur.execute("DELETE FROM bookmark WHERE u_id=%s and r_name=%s", (session['id'], r_name))
        hotplace_db.commit()
        return redirect(url_for('show_mypage'))

@app.route('/delete_user')
def delete_user():
    if 'loggedin' in session:
        cur.execute("DELETE FROM users where id=%s", session['id'])
        hotplace_db.commit()
        return redirect(url_for('logout'))

if __name__=='__main__':
    app.debug=True
    app.run(host='192.168.0.8', port=5000)