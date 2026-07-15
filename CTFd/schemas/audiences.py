from CTFd.models import AudienceMembers, Audiences, ma


class AudienceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Audiences
        include_fk = True
        dump_only = ("id",)


class AudienceMemberSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AudienceMembers
        include_fk = True
        dump_only = ("id",)
        exclude = ("user", "team", "audience")
