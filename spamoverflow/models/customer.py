from . import db 
import uuid
 
class Customers(db.Model): 
   __tablename__ = 'customers' 
   
   ID = db.Column(db.Integer, primary_key=True)
   CustomerID = db.Column(db.String)
   Priority = db.Column(db.Boolean, nullable=False)

   # This is a helper method to convert the model to a dictionary 
   def to_dict(self): 
      return { 
         'customerID': self.CustomerID, 
         'priority': self.Priority,
      } 
 
   def __repr__(self): 
      return f'<Customers {self.CustomerID} {self.Priority}>'