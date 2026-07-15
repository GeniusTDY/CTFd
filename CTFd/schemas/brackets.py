from CTFd.models import Brackets, ma


class BracketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Brackets
        include_fk = True
        dump_only = ("id",)
