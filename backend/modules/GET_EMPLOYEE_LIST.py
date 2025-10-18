import requests

def get_employee_list(api_key):
    """
    Fetch all employees and return a sorted list with their details.
    Returns a list of dictionaries containing id, firstName, lastName, email, and mobilePhoneNumber.
    """
    url = "https://mctime.com/api/v2/auth/users"
    headers = {
        "content-type": "application/json",
        "API_KEY": api_key
    }
    params = {
        "roles": "employee"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        users = data.get("items", [{}])[0].get("data", {}).get("users", [])
        
        # Create a list of employee dictionaries
        employees = []
        for user in users:
            employee = {
                "id": user.get("id"),
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "email": user.get("email"),
                "mobilePhoneNumber": user.get("mobilePhoneNumber")
            }
            employees.append(employee)
        
        # Sort by lastName, then by firstName
        employees.sort(key=lambda x: (x["lastName"] or "", x["firstName"] or ""))
        
        return employees
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []

def create_employee_variables(employees):
    """
    Create individual variables for each employee and return them as a dictionary.
    """
    employee_vars = {}
    
    for i, employee in enumerate(employees):
        # Create a safe variable name based on name or use employee number
        first_name = employee['firstName'].replace(' ', '_') if employee['firstName'] else ""
        last_name = employee['lastName'].replace(' ', '_') if employee['lastName'] else ""
        
        if first_name and last_name:
            var_name = f"employee_{first_name}_{last_name}".lower()
        elif first_name:
            var_name = f"employee_{first_name}".lower()
        elif last_name:
            var_name = f"employee_{last_name}".lower()
        else:
            var_name = f"employee_{i+1}"
        
        # Ensure unique variable names
        original_var_name = var_name
        counter = 1
        while var_name in employee_vars:
            var_name = f"{original_var_name}_{counter}"
            counter += 1
        
        employee_vars[var_name] = employee
    
    return employee_vars

# Example usage:
if __name__ == "__main__":
    import os
    # SECURITY: Load API key from environment variable
    api_key = os.getenv('MCTIME_API_KEY')
    if not api_key:
        print("ERROR: MCTIME_API_KEY environment variable not set!")
        print("Please set it in your .env file")
        exit(1)
    employees = get_employee_list(api_key)
    
    # Create individual variables for each employee
    employee_variables = create_employee_variables(employees)
    
    # Print the list format and show variable names
    print("Employee Variables Created:")
    print("=" * 50)
    
    for var_name, employee_data in employee_variables.items():
        full_name = f"{employee_data['firstName']} {employee_data['lastName']}".strip()
        if not full_name:
            full_name = "No name provided"
        
        print(f"{var_name} = {employee_data}")
        print(f"  Name: {full_name}")
        print(f"  ID: {employee_data['id']}")
        print(f"  Email: {employee_data['email'] or 'No email'}")
        print("-" * 30)
    
    print(f"\nTotal employees: {len(employees)}")
    print(f"Available variables: {list(employee_variables.keys())}")
    
    # You can now access individual employees like:
    # employee_artiol_pepaj, employee_florian_simader, etc.