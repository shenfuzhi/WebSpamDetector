from . import db

class EmailDomains(db.Model):
    __tablename__ = 'email_domains'

    DomainID = db.Column(db.Integer, primary_key=True)
    EmailID = db.Column(db.String)
    Domain = db.Column(db.String)

    def to_dict(self):
        """Return object data in easily serializable format"""
        return {
            'DomainID': self.DomainID,
            'EmailID': self.EmailID,
            'Domain': self.Domain
        }