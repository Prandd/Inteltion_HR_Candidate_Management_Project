import {
    useState
} from "react";


import type {
    FormEvent
} from "react";


import {
    useNavigate
} from "react-router-dom";


import api from "../api/axios";







interface ToolRequirement {


    name:string;


    weight:number;


    experience:number;


    recency:number;


}





interface SkillDomain {


    id:number;


    name:string;


    tools:ToolRequirement[];


}









function PositionRequirements(){



    const navigate = useNavigate();





    const [

        title,

        setTitle

    ] = useState("");





    const [

        department,

        setDepartment

    ] = useState(
        "Engineering"
    );





    const [

        location,

        setLocation

    ] = useState("");





    const [

        description,

        setDescription

    ] = useState("");






    const [

        loading,

        setLoading

    ] = useState(false);






    const [

        error,

        setError

    ] = useState("");









    const [

        domains,

        setDomains

    ] = useState<SkillDomain[]>([


        {

            id:1,

            name:"Programming",

            tools:[

                {

                    name:"Python",

                    weight:5,

                    experience:3,

                    recency:1

                }

            ]

        }



    ]);









    function addDomain(){


        setDomains(prev=>[

            ...prev,

            {

                id:Date.now(),

                name:"New Skill Domain",

                tools:[

                    {

                        name:"",

                        weight:3,

                        experience:1,

                        recency:1

                    }

                ]

            }

        ]);

    }









    function addTool(

        domainId:number

    ){


        setDomains(prev=>

            prev.map(domain=>


                domain.id===domainId

                ?

                {

                    ...domain,

                    tools:[

                        ...domain.tools,

                        {

                            name:"",

                            weight:3,

                            experience:1,

                            recency:1

                        }

                    ]

                }

                :

                domain


            )

        );

    }









    function updateDomain(

        id:number,

        value:string

    ){


        setDomains(prev=>

            prev.map(domain=>

                domain.id===id

                ?

                {

                    ...domain,

                    name:value

                }

                :

                domain

            )

        );


    }









    function updateTool(

        domainId:number,

        index:number,

        field:keyof ToolRequirement,

        value:string|number

    ){


        setDomains(prev=>

            prev.map(domain=>{


                if(domain.id!==domainId)

                    return domain;




                return {


                    ...domain,


                    tools:

                    domain.tools.map((tool,i)=>{


                        if(i!==index)

                            return tool;



                        return {


                            ...tool,


                            [field]:value


                        };


                    })


                };



            })

        );


    }









    async function publish(

        e:FormEvent

    ){


        e.preventDefault();




        if(!title.trim()){


            setError(
                "Job title is required"
            );


            return;


        }






        try{


            setLoading(true);

            setError("");





            const skills = domains.flatMap(

                domain =>

                domain.tools

                .map(tool=>tool.name)

                .filter(Boolean)

            );







            await api.post(

                "/positions",

                {

                    title,

                    department,

                    description,

                    location,

                    skills

                }

            );






            navigate("/positions");



        }


        catch(err){


            console.error(err);



            setError(
                "Failed to create position"
            );


        }


        finally{


            setLoading(false);


        }



    }









    return (



<form


onSubmit={publish}


className="

min-h-screen

bg-[#f7f9ff]

p-6

"

>



<div


className="

max-w-5xl

mx-auto

space-y-6

"

>









<button


type="button"


onClick={()=>navigate("/positions")}


className="

text-sm

text-gray-500

"

>

← Back to Positions


</button>







<h1

className="

text-3xl

font-bold

"

>

Create Position

</h1>









{

error &&


<div

className="

bg-red-50

text-red-600

px-4

py-3

rounded-xl

text-sm

"

>

{error}


</div>


}









<section

className="

bg-white

border

rounded-2xl

p-6

"

>



<h2 className="font-bold text-lg mb-5">

Position Information

</h2>





<div className="grid grid-cols-2 gap-5">



<FormInput

label="Job Title"

value={title}

onChange={setTitle}

placeholder="AI Engineer"

/>







<label>


<p className="text-sm text-gray-600">

Department

</p>



<select

value={department}

onChange={e=>setDepartment(e.target.value)}

className="mt-2 w-full border rounded-xl px-4 py-3"

>

<option>
Engineering
</option>

<option>
Data Science & AI
</option>

<option>
Product
</option>


</select>


</label>







<FormInput

label="Location"

value={location}

onChange={setLocation}

placeholder="Bangkok"

/>







<label className="col-span-2">


<p className="text-sm text-gray-600">

Description

</p>


<textarea

rows={4}

value={description}

onChange={e=>setDescription(e.target.value)}

className="mt-2 w-full border rounded-xl px-4 py-3"

/>


</label>




</div>


</section>









<section

className="

bg-white

border

rounded-2xl

p-6

"

>



<div className="flex justify-between mb-5">


<h2 className="font-bold text-lg">

Skills

</h2>


<button

type="button"

onClick={addDomain}

className="text-blue-600 text-sm"

>

+ Add Skill Domain

</button>


</div>









{

domains.map(domain=>(


<div

key={domain.id}

className="border rounded-xl p-4 mb-4"

>


<input


value={domain.name}


onChange={e=>

updateDomain(

domain.id,

e.target.value

)

}


className="font-semibold border-b pb-1"


/>





{

domain.tools.map((tool,index)=>(


<div

key={index}

className="mt-4"

>


<input


value={tool.name}


placeholder="Skill name"


onChange={e=>

updateTool(

domain.id,

index,

"name",

e.target.value

)

}


className="border rounded-lg px-3 py-2 w-full"

/>


</div>


))


}







<button


type="button"


onClick={()=>addTool(domain.id)}


className="mt-3 text-blue-600 text-sm"

>

+ Add Tool

</button>




</div>


))


}



</section>









<div className="flex justify-end gap-3">


<button


type="button"


onClick={()=>navigate("/positions")}


className="px-5 py-3 border rounded-xl"

>

Cancel

</button>





<button


disabled={loading}


className="px-6 py-3 bg-blue-600 text-white rounded-xl disabled:bg-gray-400"

>


{

loading

?

"Publishing..."

:

"Publish Position"

}



</button>



</div>








</div>



</form>



    );

}




function FormInput({

label,

value,

onChange,

placeholder

}:{

label:string;

value:string;

onChange:(v:string)=>void;

placeholder:string;

}){


return (

<label>


<p className="text-sm text-gray-600">

{label}

</p>


<input


value={value}


onChange={e=>onChange(e.target.value)}


placeholder={placeholder}


className="mt-2 w-full border rounded-xl px-4 py-3"


/>


</label>


);


}







export default PositionRequirements;