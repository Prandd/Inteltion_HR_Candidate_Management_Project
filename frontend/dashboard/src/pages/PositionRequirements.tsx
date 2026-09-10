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

        },



        {

            id:2,

            name:"Machine Learning",

            tools:[

                {

                    name:"TensorFlow",

                    weight:4,

                    experience:2,

                    recency:2

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

        toolIndex:number,

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

                    domain.tools.map((tool,index)=>{


                        if(index!==toolIndex)

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

        alert("Please enter job title");

        return;

    }






    try{


        const skills =


            domains.flatMap(domain=>

                domain.tools.map(tool=>({

                    name:tool.name,

                    domain:domain.name,

                    weight:tool.weight,

                    experience:tool.experience,

                    recency:tool.recency

                }))

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


    catch(error){


        console.error(error);


        alert(
            "Failed to create position"
        );


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








{/* HEADER */}



<div>


<button


type="button"


onClick={()=>navigate("/positions")}


className="

text-sm

text-gray-500

mb-3

"


>

← Back to Positions

</button>





<h1

className="

text-3xl

font-bold

text-gray-900

"

>

Create Position

</h1>



<p

className="

text-gray-500

mt-1

"

>

Define requirements and let AI rank candidates automatically

</p>


</div>









{/* BASIC INFORMATION */}



<section


className="

bg-white

border

rounded-2xl

p-6

"

>



<h2

className="

font-bold

text-lg

mb-5

"

>

Position Information

</h2>






<div

className="

grid

grid-cols-2

gap-5

"

>



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


className="

mt-2

w-full

border

rounded-xl

px-4

py-3

"

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

Job Description

</p>


<textarea


rows={4}


value={description}


onChange={e=>setDescription(e.target.value)}


className="

mt-2

w-full

border

rounded-xl

px-4

py-3

"


/>



</label>



</div>



</section>









{/* AI MATCHING */}



<section


className="

bg-blue-50

border

border-blue-100

rounded-2xl

p-5

"

>


<h3

className="

font-bold

text-blue-700

"

>

🤖 AI Matching Enabled

</h3>



<p

className="

text-sm

text-gray-600

mt-1

"

>

Requirement weights are used for candidate ranking and matching score.

</p>



</section>









{/* SKILLS */}



<section


className="

bg-white

border

rounded-2xl

p-6

"

>



<div


className="

flex

justify-between

items-center

mb-5

"

>


<h2

className="

font-bold

text-lg

"

>

Skill Requirements

</h2>



<button


type="button"


onClick={addDomain}


className="

text-blue-600

text-sm

font-semibold

"


>

+ Add Skill Domain

</button>


</div>









{

domains.map(domain=>(



<div


key={domain.id}


className="

border

rounded-xl

p-4

mb-4

"

>




<input


value={domain.name}


onChange={e=>

updateDomain(

domain.id,

e.target.value

)

}


className="

font-semibold

text-lg

outline-none

border-b

pb-1

"


/>







{

domain.tools.map((tool,index)=>(



<div


key={index}


className="

grid

grid-cols-4

gap-3

mt-4

"

>


<input


value={tool.name}


onChange={e=>

updateTool(

domain.id,

index,

"name",

e.target.value

)

}


placeholder="Tool / Skill"


className="

border

rounded-lg

px-3

py-2

"


/>






<Stepper


label="Weight"


value={tool.weight}


min={1}


max={5}


onChange={value=>

updateTool(

domain.id,

index,

"weight",

value

)

}


/>







<Stepper


label="Experience"


value={tool.experience}


min={0}


max={20}


onChange={value=>

updateTool(

domain.id,

index,

"experience",

value

)

}


/>







<Stepper


label="Recency"


value={tool.recency}


min={0}


max={20}


onChange={value=>

updateTool(

domain.id,

index,

"recency",

value

)

}


/>



</div>



))


}






<button


type="button"


onClick={()=>addTool(domain.id)}


className="

mt-4

text-blue-600

text-sm

font-medium

"


>

+ Add Tool

</button>




</div>



))


}



</section>









{/* ACTION */}



<div


className="

flex

justify-end

gap-3

"


>



<button


type="button"


onClick={()=>navigate("/positions")}


className="

px-5

py-3

border

rounded-xl

"


>

Cancel

</button>






<button


className="

px-6

py-3

bg-blue-600

text-white

rounded-xl

font-semibold

"


>

Publish Position

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

onChange:(value:string)=>void;

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


className="

mt-2

w-full

border

rounded-xl

px-4

py-3

"


/>


</label>


);


}









function Stepper({

label,

value,

min,

max,

onChange

}:{

label:string;

value:number;

min:number;

max:number;

onChange:(value:number)=>void;

}){


return (

<div>


<p className="text-xs text-gray-500 mb-1">

{label}

</p>



<div


className="

border

rounded-lg

flex

items-center

justify-between

px-2

py-1.5

"


>


<button


type="button"


onClick={()=>onChange(Math.max(min,value-1))}


>

-

</button>



<span className="text-sm font-medium">

{value}

</span>



<button


type="button"


onClick={()=>onChange(Math.min(max,value+1))}


>

+

</button>


</div>


</div>


);


}





export default PositionRequirements;