=====
Chess
=====

Chess is a Django app to play chess through a web browser.

Quick start
-----------

1. Add "chess" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'chess',
    ]

2. Include the chess URLconf in your project urls.py like this::

    path('chess/', include('chess.urls')),

3. Run `python manage.py migrate` to create the chess models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a poll (you'll need the Admin app enabled).

5. Visit http://127.0.0.1:8000/chess/ to participate in the poll.

