from . import db

class Emails(db.Model):
    __tablename__ = 'emails'

    ID = db.Column(db.Integer, primary_key=True)
    EmailID = db.Column(db.String)
    CustomerID = db.Column(db.String)
    CreatedAt = db.Column(db.DateTime)
    UpdatedAt = db.Column(db.DateTime)
    To = db.Column(db.String)
    From = db.Column(db.String)
    Subject = db.Column(db.String)
    Status = db.Column(db.String, default='pending')
    Malicious = db.Column(db.Boolean)
    Body = db.Column(db.Text)
    SpamHammer = db.Column(db.String)

    def to_dict(self):
        """Return object data in easily serializable format"""
        return {
            'ID': self.ID,
            'EmailID': self.EmailID,
            'CustomerID': self.CustomerID,
            'CreatedAt': self.CreatedAt,
            'UpdatedAt': self.UpdatedAt,
            'To': self.To,
            'From': self.From,
            'Subject': self.Subject,
            'Status': self.Status,
            'Malicious': self.Malicious,
            'Body': self.Body,
            'SpamHammer': self.SpamHammer
        }