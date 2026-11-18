### To Launch
Open two terminals, one in /frontend, the other in /backend.
Make sure to activate virtual env in backend and run 
```
pip install -r requirements.txt
```
Launch frontend via
```
npm run dev
```
Launch backend via
```
python manage.py runserver
```

### Preparation exam

The preparation exam uses Django to select and grade questions and save student
attempts. After installing backend dependencies, run `python manage.py migrate`
and `python manage.py seed_prep_exam`. See [the exam guide](docs/prep-exam.md) for
login/development configuration, question authoring, API details, tests, and
future local-model integration.
