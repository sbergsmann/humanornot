import json
import threading

RESULTS_JSON = 'results/results.json'

def store_results(room_data, active_ai_claims, active_human_claim):
    correctly_identified_ai = 0 # number of times a human correctly identified an AI
    incorrectly_identified_ai = 0 # number of times a human incorrectly identified an AI as a human
    correctly_identified_human = 0 # number of times any user correctly identified a human
    incorrectly_identified_human = 0 # number of times any user incorrectly identified a human as an AI
    
    users = room_data['users']
    has_ai = room_data['has_ai']

    if len(users) == 2: # both humans
        correctly_identified_human += len(active_human_claim)
        incorrectly_identified_human += len(active_ai_claims)
    elif has_ai: # one human, one AI
        # human vote
        if users[0] in active_ai_claims:
            print(len(active_ai_claims))
            correctly_identified_ai += 1
        elif users[0] in active_human_claim:
            incorrectly_identified_ai += 1
        # AI vote, assuming it can only make a human claim when the user is not behaving properly
        if len(active_human_claim) == 1 and users[0] not in active_human_claim:
            correctly_identified_human += 1

    # update results in results.json
    with open(RESULTS_JSON, 'r') as f:
        data = json.load(f)
    
    data['results']['correctly_identified_AI'] += correctly_identified_ai
    data['results']['incorrectly_identified_AI'] += incorrectly_identified_ai
    data['results']['correctly_identified_human'] += correctly_identified_human
    data['results']['incorrectly_identified_human'] += incorrectly_identified_human
    data['results']['total_games'] += 1 # increment total games

    with open(RESULTS_JSON, 'w') as f:
        json.dump(data, f, indent=4)

def read_results():
    try:
        with open(RESULTS_JSON, 'r') as f:
            results = json.load(f)
        return results['results']
    except Exception:
        return None
    
def update_results_display(results_label):
    results = read_results()
    if results:
        results_text = (
            f"Correctly identified AI: {results.get('correctly_identified_AI')}\n"
            f"Incorrectly identified AI: {results.get('incorrectly_identified_AI')}\n"
            f"Correctly identified human: {results.get('correctly_identified_human')}\n"
            f"Incorrectly identified human: {results.get('incorrectly_identified_human')}\n"
            f"Total games: {results.get('total_games')}"
        )
        
    else:
        results_text = "No results available at the moment."
    
    results_label.value = results_text
    results_label.update()
    threading.Timer(5, update_results_display, [results_label]).start()