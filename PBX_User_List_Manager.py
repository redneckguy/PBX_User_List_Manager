# import libraries
import json
import requests
import customtkinter
from tkinter import messagebox
import pandas as pd

# GUI color schema
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()

# the window title
root.title('User list Wildix API')

# main frame
frame = customtkinter.CTkFrame(root)
frame.pack(pady=20, padx=30, fill="both", expand=True)

# Main title (big letters)
label = customtkinter.CTkLabel(frame, text="User list Wildix API", font=("Roboto", 24))

# field for PBX domain name entry
entry_pbx_name = customtkinter.CTkEntry(frame, placeholder_text='Please enter PBX domain name', width=210)

# field for PBX token entry
entry_token = customtkinter.CTkEntry(frame, placeholder_text="Please paste bearer token", width=210)


# class for authorization (using bearer token)
class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


# function to get user list and export it to csv file
def get_userlist() -> None:
    # settings token and PBX name variables
    token = entry_token.get()
    pbx_name = entry_pbx_name.get()
    # checking if both exist
    if token and pbx_name:
        # API link request
        api_req = f"https://{pbx_name}.wildixin.com/api/v1/Colleagues/"
        try:
            response = requests.get(api_req, auth=BearerAuth(token))
            # getting needed content from API json response
            records = response.json()['result']['records']
            with open('original_user_list.json', 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=4)
            # warning message if incorrect token
            if response.json()['type'] == 'error':
                messagebox.showwarning("Incorrect credentials", "Please try another token!")
            # pandas buffering JSON response
            df = pd.DataFrame(records)
            # pandas exporting users into csv file that we will correct
            df.to_csv('userlist.csv', encoding='utf-8', index=False)
            messagebox.showinfo("SUCCESS!", "User list has been successfully imported!")
        #  exception for incorrect PBX name
        except Exception as e:
            print(e)
            messagebox.showwarning("Incorrect credentials", "Incorrect PBX name!")
    # if PBX name / token field is empty
    else:
        messagebox.showwarning("LACK OF DATA!", "You haven't entered your credentials")


# button for saving PBX name / token and request the user list
button_save_cred = customtkinter.CTkButton(frame, text="Get user list", command=get_userlist)


# function to update users
def update_users() -> None:
    # export csv to temporary json file
    dtypes = {"officePhone": str, "mobilePhone": str, 'faxNumber': str, "department": str, "id": str, "extension": str,
              "email": str}
    df = pd.read_csv("userlist.csv", dtype=dtypes, encoding="utf-8")
    data = df.to_dict(orient="records")
    with open("temp.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # pandas adds NaN instead of "" so need to replace all NaN's for correct comparing
    with open("temp.json", "r") as f:
        data = json.load(f)
    json_string = json.dumps(data).replace("NaN", '""')
    with open("corrected_userlist.json", "w") as f:
        f.write(json_string)

    headers = {"Authorization": f"Bearer {entry_token.get()}"}

    #  comparing dictionaries in the original and new json files
    with open('original_user_list.json') as f1, open('corrected_userlist.json') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    for d2 in data2:
        if 'id' in d2 and d2['id'].isdigit():
            for d1 in data1:
                if int(d2['id']) == int(d1['id']):
                    if d2.items() == d1.items():
                        break
                    else:
                        print("the other keys values are not the same:", d2)

                        data = {}
                        for key, value in d2.items():
                            if key not in ["dn", "id", "pbxDn", "picture", "sourceId", "jid"]:
                                data[key] = value

                        print(data)

                        url = f"https://{entry_pbx_name.get()}.wildixin.com/api/v1/PBX/Colleagues/{d2['id']}/"
                        try:
                            r = requests.put(url, headers=headers, json=data)
                            r.raise_for_status()  # raises an exception for non-2XX responses
                            print(f"API PUT request sent to {url}")
                        except requests.exceptions.RequestException as e:
                            print(f"Error sending API PUT request to {url}: {e}")
                        break
            else:
                print("id value is not the same:", d2)
                new_user = {key: value for key, value in d2.items() if value and key not in ["id"]}
                print(new_user)

                url = f"https://{entry_pbx_name.get()}.wildixin.com/api/v1/PBX/Colleagues/"
                try:
                    r = requests.post(url, headers=headers, json=new_user)
                    r.raise_for_status()  # raises an exception for non-2XX responses
                    print(f"API POST request sent to {url}")
                except requests.exceptions.RequestException as e:
                    print(f"Error sending API PUT request to {url}: {e}")
        else:
            print("no id but other keys values:", d2)
            new_user_no_id = {key: value for key, value in d2.items() if value}
            url = f"https://{entry_pbx_name.get()}.wildixin.com/api/v1/PBX/Colleagues/"
            try:
                r = requests.post(url, headers=headers, json=new_user_no_id)
                r.raise_for_status()  # raises an exception for non-2XX responses
                print(f"API POST request sent to {url}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending API POST request to {url}: {e}")

    messagebox.showinfo("Comparing is completed!", "Comparing of user lists is completed!")


# button to update users
button_update_users = customtkinter.CTkButton(frame, text="Update users", command=update_users)

# entry for extensions/ids that need to be deleted
entry_collg_id = customtkinter.CTkEntry(frame, placeholder_text="Delete ext's (ex. ext1,ext2,ext3)", width=210)


def delete_users() -> None:
    # read the json file
    with open("original_user_list.json", "r") as f:
        users = json.load(f)

    # get the input ids or extensions
    input_ids = entry_collg_id.get().split(",")

    # initialize a list to store the actual ids corresponding to the input ids or extensions
    actual_ids = []

    # loop through the input ids or extensions and find the corresponding actual ids
    for input_id in input_ids:
        found_user = None
        for user in users:
            if input_id == user["id"] or input_id == user["extension"]:
                found_user = user
                break
        if found_user is not None:
            actual_ids.append(found_user["id"])
        else:
            messagebox.showwarning("No id's", f"User ID/extension '{input_id}' not found!")

    # build the API url and send the request with multiple actual ids
    headers = {"Authorization": f"Bearer {entry_token.get()}"}
    actual_ids_str = ",".join(actual_ids)
    if actual_ids_str:
        try:
            url = f"https://{entry_pbx_name.get()}.wildixin.com/api/v1/PBX/Colleagues/{actual_ids_str}/?deletePersonData=0"
            r = requests.delete(url, headers=headers)
            r.raise_for_status()  # raises an exception for non-2XX responses
            print(f"API POST request sent to {url}")
            messagebox.showinfo("Deletion has been completed!", "Deletion of the user(s) has been completed!!")
        except requests.exceptions.RequestException as e:
            print(f"Error sending API POST request to {url}: {e}")
    else:
        messagebox.showwarning("No id's", f"User ID(s)/extension(s) hasn't been entered")


# button to delete users
button_delete_users = customtkinter.CTkButton(frame, text="Delete users", command=delete_users)

# x and y padding for interface elements
for widget in frame.winfo_children():
    widget.pack_configure(pady=12, padx=20)

# GUI running (looping) function
root.mainloop()
