# Function that creates a message containing a list of all predictions
def create_message_categories(ans):
    text = ""
    for i in ans:
        category = i[0]

        text += f"<tr><td> {str(category)} </td></tr>"
    message = ("<table><tr><th>" + " Your categories: " + "</th></tr>" + text
               + "</table>")
    return message

# Function that creates a message containing a list of all predictions
def create_message_select_query(ans):
    text = ""
    for i in ans:
        id = i[0]
        date = i[2]
        task_description = i[3]
        task_category = i[4]
        unit_of_measure = i[5]
        pred_low_50_conf = i[6]
        pred_high_50_conf = i[7]
        pred_low_90_conf = i[8]
        pred_high_90_conf = i[9]
        actual_outcome = i[10]

        text += (f"{str(id)} | {date} | {task_description} | "
                 f"{task_category} | {unit_of_measure} | "
                 f"{str(pred_low_50_conf)} | {str(pred_high_50_conf)} | "
                 f"{str(pred_low_90_conf)} | {str(pred_high_90_conf)} | "
                 f"{str(actual_outcome)}\n")
    message = "You have made predictions:\n\n"+text
    return message