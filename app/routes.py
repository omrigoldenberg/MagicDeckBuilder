import copy

from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import app, db, deckbuilder
from app.classes import GuideHold, Guide
from app.deckbuilder import get_sb
from app.forms import LoginForm, RegistrationForm, DeckBuilderForm, SideForm, ViewForm, VoteForm
from app.models import User, DeckStore


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return profile()

    posts = DeckStore.query.filter_by(hidden=False)
    for post in posts:
        print(post.deck)
    return render_template('index.html', title='Home', decklist=posts)

@login_required
@app.route('/profile')
def profile():
    yours = DeckStore.query.filter_by(user_id=grab_user())
    theres = DeckStore.query.filter_by(hidden=False).filter(DeckStore.user_id != grab_user())
    return render_template('home.html', title='Profile', private_decklist=yours, public_decklist=theres)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/build', methods=['GET', 'POST'])
@login_required
def build():
    user = grab_user()
    if user is None:
        flash('Invalid login')
        return redirect(url_for('login'))
    form = DeckBuilderForm()
    if form.validate_on_submit():
        body:str = form.deckfield.data
        side:str = form.sidefield.data
        name:str = form.namefield.data
        format:str = form.formatfield.data
        hidden= form.hidden.data
        list_body = body.split('\n')
        list_side = side.split('\n')
        list_body.append("")
        list_body = list_body + list_side
        deck = deckbuilder.pipeline(list_body, name=name, tournament=format)
        if deck is None:
            flash('Errors in deck!', 'error')
            return redirect(url_for('build', deck = deck))
        else:
            db.session.add(DeckStore(deck=deck, user_id=user, hidden=hidden, guides=GuideHold()))  # TODO: also add hidden option.
            db.session.commit()
            flash('Deck submitted successfully')
            return redirect(url_for('index'))
    return render_template('deckbuilder.html', title='Make a Deck', form=form)

@app.route('/view/<int:deck>', methods=['GET', 'POST'])
def view(deck: int):
    user = grab_user()
    query = DeckStore.query.filter_by(id=deck).first()
    form = ViewForm()
    if request.method == 'POST':
        return redirect(url_for('submit', deck = deck))
    if query.hidden:
        if user is None:
            flash('Insufficient permission', 'danger')
            abort(401)
        elif user == query.user_id:
            deck = query.deck
            return render_template('deckviewer.html', title=f'{deck.name} by {query.user_id} (Hidden)', deck=deck, form = form, l = len(query.guides.list))
        else:
            flash('Insufficient permission', 'danger')
            abort(403)
    else:
        deck = query.deck
        return render_template('deckviewer.html', title=f'{deck.name} by {query.user_id}', deck=deck, form = form, id = query.id, l = len(query.guides.list))


@login_required
@app.route('/view/<int:deck>/submit', methods=['GET', 'POST'])
def submit(deck: int):
    user = grab_user()
    query = DeckStore.query.filter_by(id=deck).first()
    if user is None:
        flash('Invalid login', 'danger')
        return redirect(url_for('login'))
    form = SideForm()
    if form.validate_on_submit():
        out =  get_sb(form.side_out.data,query.deck,False)
        In = get_sb(form.side_in.data,query.deck,True)
        print(out)
        print(In)
        if In is None or out is None:
            print("here")
            flash('Errors in guide!', 'error')
            return redirect(url_for('submit', deck = deck))
        message = form.explanation.data
        g = Guide(In,out,message)
        guides  = copy.deepcopy(query.guides)
        guides.add(g)
        query.guides = guides
        db.session.commit()
        flash('Submitted guide number: ' + str(len(query.guides.list)-1)) # Guides are numbered from 0
        return redirect(url_for('view', deck = deck))

    deck = query.deck
    return render_template('sideboard_submit.html', title=f'{deck.name} by {query.user_id}', deck=deck, form=form)

@app.route('/view/<int:deck>/<int:guide_num>', methods=['GET', 'POST'])
def viewsb(deck, guide_num):
    user = grab_user()
    if user is not None:
        form = VoteForm()
    else:
        form = None
    query = DeckStore.query.filter_by(id=deck).first()
    guide_list = copy.deepcopy(query.guides)
    guide = guide_list.get(guide_num)
    if request.method == 'POST' and user is not None:
        if form.up.data:
            guide.up[user] = 1
            if user in guide.down.keys():
                guide.down.pop(user)
        if form.down.data:
            guide.down[user] = 1
            if user in guide.up.keys():
                guide.up.pop(user)
        query.guides = guide_list
        db.session.commit()
        redirect(url_for('viewsb', deck = deck, guide_num = guide_num))
    deck = query.deck
    red = []
    nonred = []
    for card in deck.main_deck:
        check = 0
        for card2 in guide.to_side:
            if card2[1].name == card[1].name:
                red.append((card,card2[0]))
                check = 1
        if check == 0:
            nonred.append(card)
    green = []
    nongreen = []
    for card in deck.sideboard:
        check = 0
        for card2 in guide.from_side:
            if card2[1].name == card[1].name:
                green.append((card,card2[0]))
                check = 1
        if check == 0:
            nongreen.append(card)

    deck = query.deck
    if user is not None:
        return render_template('guideviewer.html', title=f'{deck.name} by {query.user_id}', deck=deck, green = green, red = red, nongreen = nongreen, nonred = nonred, guide = guide, form = form)
    return render_template('guideanonview.html', title=f'{deck.name} by {query.user_id}', deck=deck, green=green, red=red, nongreen=nongreen, nonred=nonred, guide=guide)


# Forbidden
@app.errorhandler(403)
def forbidden(e):
    return render_template('forbidden.html', title='403 Error', error=403, message="You do not have access to this resource."), 403

# Authenticate
@app.errorhandler(401)
def authentication_need(e):
    return render_template('forbidden.html', title='401 Error', error=401, message="You must log in to view this resource"), 401  # Todo: make this more complete.

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    # return render_template('register.html')
    return render_template('register.html', title='Register', form=form)

def grab_user():
    if current_user.is_authenticated:
        return current_user.id
    else:
        return None
