from wtforms import Form, StringField,PasswordField,TextAreaField,DateField,SubmitField,IntegerField, BooleanField,  validators
from wtforms.fields import EmailField,DateTimeField
import matplotlib.pyplot as pyplot
import numpy as np

class RegistrationForm(Form):
    addhar=StringField('Addhar',[validators.DataRequired("Please Enter your Addhar Number"),validators.Regexp(regex=r'\d{12}$',message="Aadhar must be of 12 Digits")])
    name=StringField('Name',[validators.Length(min=1, max=100)])
    email=EmailField('Email',[validators.Email()])
    mobile=StringField('Mobile',[validators.DataRequired("Please Enter your Mobile Number"),validators.Regexp(regex=r'\d{10}$',message="Mobile Number must be of 10 Digits")])
    password=PasswordField('Password',[
    validators.Length(min=8, max=50),
    validators.DataRequired("Please Enter Password"),
    validators.EqualTo('confirm_password', message="Password does not match")
    ])
    confirm_password=PasswordField('Confirm Password')
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice', [validators.DataRequired()])


#class for vaiation grph plotting
class plot_variation_graph():
    x=[]
    y=[]
    graph_title=""
    graph_xlabel=""
    graph_ylabel=""
    graph_color_style=""
    def __init__(self,x,y,graph_title,graph_xlabel,graph_ylabel,graph_color_style):
        self.x=x
        self.y=y
        self.graph_title=graph_title
        self.graph_xlabel=graph_xlabel
        self.graph_ylabel=graph_ylabel
        self.graph_color_style=graph_color_style
        pyplot.close('all')

    def make_plot(self):
        index=np.arange(len(self.x))
        pyplot.plot(index,self.y,self.graph_color_style)
        pyplot.title(self.graph_title)
        pyplot.xlabel(self.graph_xlabel)
        pyplot.ylabel(self.graph_ylabel)
        pyplot.xticks(index,self.x,fontsize=10,rotation=30)
        pyplot.show()
        pyplot.close()


#class for Bar grph plotting
class plot_bar_graph():
    x=[]
    y=[]
    graph_title=""
    graph_xlabel=""
    graph_ylabel=""
    width=""

    def __init__(self,x,y,graph_title,graph_xlabel,graph_ylabel,width):
        self.x=x
        self.y=y
        self.graph_title=graph_title
        self.graph_xlabel=graph_xlabel
        self.graph_ylabel=graph_ylabel
        self.width=width
        pyplot.close('all')

    def make_plot(self):
        index=np.arange(len(self.x))
        pyplot.bar(index,self.y,self.width)
        pyplot.title(self.graph_title)
        pyplot.xlabel(self.graph_xlabel)
        pyplot.ylabel(self.graph_ylabel)
        pyplot.xticks(index,self.x,fontsize=10,rotation=30)
        pyplot.show()
        pyplot.close()



#class for Pi grph plotting
class plot_pi_graph():
    labels=[]
    sizes=[]
    graph_title=""
    explode=[]


    def __init__(self,labels,sizes,graph_title):
        self.labels=labels
        self.sizes=sizes
        self.graph_title=graph_title
        self.explode=[]
        pyplot.close('all')

    def make_plot(self):
        for i in range(len(self.sizes)):
            self.explode.append(0.1)
        self.explode=tuple(self.explode)
        # Plot
        pyplot.pie(self.sizes,labels=self.labels,explode=self.explode,autopct='%1.1f%%', shadow=True, startangle=140)
        pyplot.axis('equal')
        pyplot.title(self.graph_title)
        pyplot.show()
        pyplot.close()
