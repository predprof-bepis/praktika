import dbtools

db = dbtools.DB(autosave=False)

db.add_programs([["a", 1], ["b", 2]])

print(db.get_program(1))
print("-"*50)
print(db.get_program())
db.update_program_by_id([["a", 1337, 1]])
print("updated!")
print(db.get_program())
db.add_application([["a", 1337, 1]])