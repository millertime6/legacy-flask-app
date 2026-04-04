from app.models.contact import Contact
from app.utils.serialization import model_to_dict


def get_contact_by_external_id(external_id: str):
    contact = Contact.query.filter_by(external_id=external_id).first()
    if not contact:
        return None
    return model_to_dict(contact)
