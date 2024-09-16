from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
import pandas as pd

def index(request):
    data_dir = "/Users/katybarone/Documents/projects/tennis/"
    atp = pd.read_csv(data_dir + "atp_100_withIDs.csv")
    player_list = atp.name.values
    template = loader.get_template("preds/index.html")
    context = {"player_list": player_list}

    return HttpResponse(template.render(context, request))

def pick_player(request):
    #return HttpResponse("this is the pick_player view!")
    if request.method == 'POST':
        player1 = request.POST.get('player1')  # Get the selected player from POST data
        player2 = request.POST.get('player2')
        # Now you can do something with `selected_player`
        # For example, return a new template or render the same template with some result
        #return render(request, 'player_result.html', {'selected_player': selected_player})
        return HttpResponse("you selected {} and {}".format(player1, player2))
    return redirect(index)  # Handle case if accessed via GET (optional)
